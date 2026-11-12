"""Stage 4 - from deliveries to a ranked shortlist.

Every ball is scored as runs above (or below) what the situation normally
yields, with wickets priced in runs off the fitted resource curve:

    batter impact = (runs - xRuns) - wicketCost * (out - xWicket)
    bowler impact = (xRuns - runs) + wicketCost * (wicket - xWicket)

Expectations are conditioned on the pressure band itself, so a player is judged
against what others actually manage in comparable situations rather than
against their own easy-overs form.

Rather than throwing away 87% of the data behind a hard pressure cut-off, every
delivery contributes with a weight set by its Pressure Index. Ratings are then
shrunk toward the league mean in proportion to effective sample size, so a
player cannot top the table on a handful of lucky deliveries.
"""
import json

import numpy as np
import pandas as pd

from common import OUT, TIER1, zscore, shrink
from model_lib import hierarchical_mean
import reliability as relmod

RECENCY_DECAY = 0.78        # weight applied per season before 2026
PRESS_FLOOR = 45            # PI below this carries no pressure weight
PRESS_GAMMA = 1.5           # convexity: emphasise the genuinely hard balls

K_BAT, K_BOWL = 70.0, 70.0  # shrinkage ballast, in pressure-weighted balls
K_REL = 8.0                 # shrinkage ballast for reliability, in matches

MIN_W_BAT, MIN_W_BOWL = 45.0, 45.0
MIN_MATCHES = 12
# Every ranked player must actually have been out there: a floor on raw
# pressure deliveries, so nobody is ranked on their calm-overs record alone.
MIN_PRESS_BALLS = 90
MIN_BALLS_BAT, MIN_BALLS_BOWL = 400, 400


def opposition_tiers(bb):
    """Rate every team's attack and batting from the data, not from reputation.

    Expectations must depend on who you were up against: 1.4 runs a ball off a
    weak attack is not the same feat as 1.4 off a strong one. Teams are graded
    on their own league-wide record across the dataset, then split into terciles
    weighted by how many balls they actually bowled or faced.
    """
    bowl_str = bb.groupby("bowling_team").agg(
        conceded=("total_runs", "mean"), balls=("total_runs", "size"))
    bat_str = bb.groupby("batting_team").agg(
        scored=("total_runs", "mean"), balls=("total_runs", "size"))
    # Teams with very little data sit in the middle band rather than the tails.
    def band(s, counts, lo, hi):
        q = s.copy()
        q[counts < 1500] = s.median()
        return pd.cut(q, [-np.inf, q.quantile(lo), q.quantile(hi), np.inf],
                      labels=["A", "B", "C"])
    attack = band(bowl_str.conceded, bowl_str.balls, 0.33, 0.67)   # A = meanest attack
    batting = band(bat_str.scored, bat_str.balls, 0.33, 0.67)      # C = strongest batting
    return attack, batting


def context_tier(bb, attack, batting):
    comp = np.where(bb.is_dev_comp, "dev",
                    np.where(bb.match_format == "T20I", "t20i", "ipl"))
    # A batter's context is the attack he faced; a bowler's is the batting he
    # bowled at.
    bat_ctx = pd.Series(comp, index=bb.index) + "_" + \
        bb.bowling_team.map(attack).astype(str)
    bowl_ctx = pd.Series(comp, index=bb.index) + "_" + \
        bb.batting_team.map(batting).astype(str)
    return bat_ctx, bowl_ctx


def season_year(s):
    return pd.to_numeric(s.astype(str).str.slice(0, 4), errors="coerce").fillna(2022)


DEFAULTS = dict(recency_decay=RECENCY_DECAY, press_floor=PRESS_FLOOR,
                press_gamma=PRESS_GAMMA, min_w=MIN_W_BAT, min_matches=MIN_MATCHES,
                min_press_balls=MIN_PRESS_BALLS, pi_weights=None,
                weight_mode="reliability")


def recompute_pi(bb, piw):
    """Rebuild the Pressure Index from its stored pillars under new weights."""
    wl, wa, ws, wb = piw
    mult = np.where(bb.knock_out == 1, 1.08, 1.0)
    common = wl * bb.p_leverage + ws * bb.p_scarcity
    bb["pi_bat"] = np.clip(100 * (common + wa * bb.p_adv_bat + wb * bb.p_build_bat) * mult, 0, 100)
    bb["pi_bowl"] = np.clip(100 * (common + wa * bb.p_adv_bowl + wb * bb.p_build_bowl) * mult, 0, 100)
    bb["is_press_bat"] = (bb.pi_bat >= 65).astype(int)
    bb["is_press_bowl"] = (bb.pi_bowl >= 65).astype(int)
    return bb


def prepare(bb, cfg=None):
    cfg = {**DEFAULTS, **(cfg or {})}
    bb = bb.copy()
    if cfg["pi_weights"]:
        bb = recompute_pi(bb, cfg["pi_weights"])
    attack, batting = opposition_tiers(bb)
    bb["bat_ctx"], bb["bowl_ctx"] = context_tier(bb, attack, batting)
    bb["ctx"] = bb.bat_ctx
    bb.attrs["attack_tiers"] = attack.to_dict()
    bb.attrs["batting_tiers"] = batting.to_dict()
    bb["ovb"] = pd.cut(bb.phase_over, [0, 6, 11, 15, 17, 20],
                       labels=["1-6", "7-11", "12-15", "16-17", "18-20"])
    bb["wlb"] = pd.cut(bb.wkts_left, [-1, 4, 6, 8, 10],
                       labels=["<=4", "5-6", "7-8", "9-10"])
    bb["pib_bat"] = pd.cut(bb.pi_bat, [0, 35, 50, 65, 80, 100],
                           labels=["b1", "b2", "b3", "b4", "b5"])
    bb["pib_bowl"] = pd.cut(bb.pi_bowl, [0, 35, 50, 65, 80, 100],
                            labels=["b1", "b2", "b3", "b4", "b5"])
    bb["syear"] = season_year(bb.season)
    bb["w_rec"] = cfg["recency_decay"] ** (2026 - bb.syear).clip(lower=0)

    bb["striker_out"] = (bb.is_wicket & (bb.dismissed_player_id == bb.striker_id)).astype(float)
    bb["bat_runs"] = bb.runs.astype(float)
    return bb


def press_weights(pi, floor=PRESS_FLOOR, gamma=PRESS_GAMMA):
    u = np.clip((pi - floor) / (100.0 - floor), 0, 1)
    return u ** gamma, (1 - u)


def expectations(bb):
    """State-conditional xRuns and xWicket for each role."""
    bat = bb[bb.legal == 1].copy()
    levels_b = [["bat_ctx", "ovb", "wlb", "pib_bat", "pace_or_spin"],
                ["bat_ctx", "ovb", "pib_bat", "pace_or_spin"],
                ["ovb", "wlb", "pib_bat"],
                ["ovb", "pib_bat"]]
    xb, lvl_b = hierarchical_mean(bat, ["bat_runs", "striker_out"], levels_b, min_n=200)
    bat["xr"], bat["xw"] = xb.bat_runs, xb.striker_out
    bat["exp_level"] = lvl_b

    bowl = bb.copy()
    bowl["bowler_runs"] = bowl.bowler_runs.astype(float)
    bowl["bowler_wicket"] = bowl.bowler_wicket.astype(float)
    levels_l = [["bowl_ctx", "ovb", "wlb", "pib_bowl", "pace_or_spin"],
                ["bowl_ctx", "ovb", "pib_bowl", "pace_or_spin"],
                ["ovb", "wlb", "pib_bowl"],
                ["ovb", "pib_bowl"]]
    xl, lvl_l = hierarchical_mean(bowl, ["bowler_runs", "bowler_wicket"], levels_l, min_n=200)
    bowl["xr"], bowl["xw"] = xl.bowler_runs, xl.bowler_wicket
    bowl["exp_level"] = lvl_l
    return bat, bowl


def score_balls(bat, bowl, cfg=None):
    cfg = {**DEFAULTS, **(cfg or {})}
    fl, gm = cfg["press_floor"], cfg["press_gamma"]

    wc = bat.wicket_cost.to_numpy()
    bat["impact"] = (bat.bat_runs - bat.xr) - wc * (bat.striker_out - bat.xw)
    wp, wn = press_weights(bat.pi_bat.to_numpy(), fl, gm)
    bat["w_press"] = wp * bat.w_rec
    bat["w_calm"] = wn * bat.w_rec

    wc2 = bowl.wicket_cost.to_numpy()
    bowl["impact"] = (bowl.xr - bowl.bowler_runs) + wc2 * (bowl.bowler_wicket - bowl.xw)
    wp2, wn2 = press_weights(bowl.pi_bowl.to_numpy(), fl, gm)
    bowl["w_press"] = wp2 * bowl.w_rec
    bowl["w_calm"] = wn2 * bowl.w_rec
    return bat, bowl


def wmean(v, w):
    s = w.sum()
    return (v * w).sum() / s if s > 0 else np.nan


def aggregate(df, id_col, name_col, press_flag):
    """Per-player pressure record, plus match-level consistency."""
    g = df.groupby([id_col, name_col], sort=False)
    agg = g.apply(lambda d: pd.Series({
        "balls": len(d),
        "press_balls": int(d[press_flag].sum()),
        "w_press": d.w_press.sum(),
        "w_calm": d.w_calm.sum(),
        "w_all": d.w_rec.sum(),
        "n_eff": (d.w_press.sum() ** 2) / max((d.w_press ** 2).sum(), 1e-9),
        "impact_press": wmean(d.impact, d.w_press),
        "impact_calm": wmean(d.impact, d.w_calm),
        "impact_all": wmean(d.impact, d.w_rec),
        "matches": d.match_id.nunique(),
        "last_season": d.syear.max(),
        "ipl_balls": int(d.match_format.eq("T20").sum()),
        "bat_pos": d.batting_order.median(),
    }), include_groups=False).reset_index()

    # Match-level consistency: how often does the player finish a game with a
    # positive pressure contribution, rather than averaging out to it?
    rel = relmod.match_consistency(df, id_col).reset_index()
    agg = agg.merge(rel, on=id_col, how="left")
    agg["press_matches"] = agg.press_matches.fillna(0)
    agg["pos_rate"] = agg.pos_rate.fillna(0.5)
    return agg


def rate(agg, rel_res, min_w, label, cfg=None):
    """Hierarchical estimate of true performance under pressure.

    The split-half analysis says a player's raw pressure record is mostly
    noise, while their overall record repeats well. So rather than shrinking
    pressure performance toward the league average, we shrink it toward *that
    player's own overall standard* - the statistically correct prior, and also
    what a selector does by instinct: a quality player is assumed to cope until
    their pressure record says otherwise, loudly and repeatedly.
    """
    cfg = {**DEFAULTS, **(cfg or {})}
    d = agg[(agg.w_press >= min_w) & (agg.matches >= cfg["min_matches"])
            & (agg.press_balls >= cfg["min_press_balls"])].copy()
    # Rank players in the role a franchise would actually buy them for. A No. 8
    # who hits well under pressure is a useful asset, but he is not a pick on
    # a list of the ten best batters.
    if label == "batter":
        d = d[(d.bat_pos <= 7) & (d.balls >= MIN_BALLS_BAT)]
    else:
        d = d[d.balls >= MIN_BALLS_BOWL]
    d = d.copy()
    met = rel_res["metrics"]
    k_all = met["overall"]["implied_ballast_k"]
    k_press = met["press"]["implied_ballast_k"]
    k_clutch = met["clutch"]["implied_ballast_k"]
    k_rel = met.get("pos_rate", {}).get("implied_ballast_k", K_REL)

    league_impact = wmean(d.impact_all, d.w_all)
    prior_rel = float((d.pos_rate * d.press_matches).sum() / d.press_matches.sum())

    # Level 1: the player's own durable standard.
    d["overall_hat"] = shrink(d.impact_all, d.w_all, league_impact, k_all)
    # Level 2: pressure record, pulled back toward that standard.
    d["press_hat"] = shrink(d.impact_press, d.w_press, d.overall_hat, k_press)
    d["clutch_raw"] = d.impact_press - d.impact_calm
    d["clutch_hat"] = shrink(d.clutch_raw, np.minimum(d.w_press, d.w_calm), 0.0, k_clutch)
    d["consistency_hat"] = shrink(d.pos_rate, d.press_matches, prior_rel, k_rel)

    d["z_press"] = zscore(d.press_hat)
    d["z_consistency"] = zscore(d.consistency_hat)
    d["z_clutch"] = zscore(d.clutch_hat)

    # Components earn their weight rather than being assigned one. Each base
    # weight is scaled by the square root of that component's measured
    # full-length reliability, then renormalised. A component that does not
    # repeat across halves of the data cannot drive the ranking - which is why
    # batting "clutch" ends up near-decorative and bowling consistency does not.
    base = {"press": 0.65, "consistency": 0.20, "clutch": 0.15}
    rel_of = {"press": met["press"]["full_length_r"],
              "consistency": met.get("pos_rate", {}).get("full_length_r", 0.01),
              "clutch": met["clutch"]["full_length_r"]}
    if cfg["weight_mode"] == "reliability":
        raw_w = {k: base[k] * np.sqrt(max(rel_of[k], 0.0)) for k in base}
    elif cfg["weight_mode"] == "equal":
        raw_w = {k: 1.0 for k in base}
    else:                                   # "base" - the unadjusted priors
        raw_w = dict(base)
    tot = sum(raw_w.values())
    w = {k: v / tot for k, v in raw_w.items()}

    d["composite"] = (w["press"] * d.z_press
                      + w["consistency"] * d.z_consistency
                      + w["clutch"] * d.z_clutch)
    d["superrr"] = (50 + 10 * d.composite).round(1)
    d = d.sort_values("composite", ascending=False).reset_index(drop=True)
    d["rank"] = np.arange(1, len(d) + 1)
    d["role"] = label
    meta = {"league_impact": float(league_impact), "prior_consistency": prior_rel,
            "pool": int(len(d)),
            "ballasts": {"overall": k_all, "press": k_press,
                         "clutch": k_clutch, "consistency": k_rel},
            "weights": {k: round(float(v), 3) for k, v in w.items()},
            "component_reliability": {k: round(float(v), 4) for k, v in rel_of.items()}}
    return d, meta


def run(raw=None, cfg=None):
    """Full stage-4 pass. Returns ranked batters, ranked bowlers and metadata."""
    cfg = {**DEFAULTS, **(cfg or {})}
    raw = pd.read_parquet(OUT / "balls_pressure.parquet") if raw is None else raw
    bb = prepare(raw, cfg)
    bat, bowl = expectations(bb)
    bat, bowl = score_balls(bat, bowl, cfg)

    rel_bat = relmod.assess(bat, "striker_id")
    rel_bowl = relmod.assess(bowl, "bowler_id")

    ab = aggregate(bat, "striker_id", "striker_name", "is_press_bat")
    al = aggregate(bowl, "bowler_id", "bowler_name", "is_press_bowl")
    rb, mb = rate(ab, rel_bat, cfg["min_w"], "batter", cfg)
    rl, ml = rate(al, rel_bowl, cfg["min_w"], "bowler", cfg)
    mb["reliability"], ml["reliability"] = rel_bat, rel_bowl
    return rb, rl, mb, ml, bat, bowl


def main():
    rb, rl, mb, ml, bat, bowl = run()
    rel_bat, rel_bowl = mb["reliability"], ml["reliability"]
    relmod.report(rel_bat, "BATTING")
    relmod.report(rel_bowl, "BOWLING")

    bat.to_parquet(OUT / "bat_balls.parquet", index=False)
    bowl.to_parquet(OUT / "bowl_balls.parquet", index=False)
    rb.to_parquet(OUT / "rank_batters.parquet", index=False)
    rl.to_parquet(OUT / "rank_bowlers.parquet", index=False)
    with open(OUT / "diag_ratings.json", "w") as f:
        json.dump({"batting": mb, "bowling": ml,
                   "reliability_batting": rel_bat, "reliability_bowling": rel_bowl,
                   "params": {"recency_decay": RECENCY_DECAY, "press_floor": PRESS_FLOOR,
                              "press_gamma": PRESS_GAMMA, "min_matches": MIN_MATCHES,
                              "min_w_bat": MIN_W_BAT, "min_w_bowl": MIN_W_BOWL,
                              "weights": {"press_hat": 0.65, "consistency": 0.20,
                                          "clutch": 0.15}}},
                  f, indent=2, default=float)

    cols = ["rank", "striker_name", "superrr", "press_balls", "matches", "impact_all",
            "impact_press", "press_hat", "clutch_raw", "pos_rate"]
    print(f"\nEligible batters: {mb['pool']}  |  ballasts {mb['ballasts']}")
    print(rb[cols].head(15).round(3).to_string(index=False))
    cols2 = [c if c != "striker_name" else "bowler_name" for c in cols]
    print(f"\nEligible bowlers: {ml['pool']}  |  ballasts {ml['ballasts']}")
    print(rl[cols2].head(15).round(3).to_string(index=False))


if __name__ == "__main__":
    main()
