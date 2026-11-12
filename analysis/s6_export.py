"""Stage 6 - export everything the dashboard renders.

One JSON bundle per concern, written into the Next.js app's data directory.
The pressure calculator is backed by a precomputed grid rather than a
reimplementation of the models in JavaScript, so the numbers on screen are
exactly the numbers the pipeline produced.
"""
import json
import pickle
from pathlib import Path

import numpy as np
import pandas as pd

from common import DATA, OUT
import s2_models as S2
import s3_pressure as S3

WEB = Path(__file__).parent.parent / "dashboard" / "src" / "data"
WEB.mkdir(parents=True, exist_ok=True)

RR_TEAM = "Rajasthan Royals"
TOP_N = 40


def jdump(obj, name):
    with open(WEB / name, "w") as f:
        json.dump(obj, f, separators=(",", ":"), default=_enc)
    print(f"  {name:28s} {(WEB / name).stat().st_size / 1024:8.1f} KB")


def _enc(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return None if np.isnan(o) else round(float(o), 5)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, pd.Timestamp):
        return o.strftime("%Y-%m-%d")
    return str(o)


def clean(df):
    return json.loads(df.to_json(orient="records", date_format="iso"))


# --------------------------------------------------------------------------- #
def player_profiles(balls, ranks, consensus, id_col, name_col, pi_col, press_col, role):
    """Per-player splits, trends and signature performances."""
    top_ids = consensus.head(TOP_N)[id_col].tolist()
    extra = ranks.head(TOP_N)[id_col].tolist()
    ids = list(dict.fromkeys(top_ids + extra))
    d = balls[balls[id_col].isin(ids)].copy()

    rmap = ranks.set_index(id_col)
    cmap = consensus.set_index(id_col)
    profiles = []

    for pid, g in d.groupby(id_col):
        if pid not in rmap.index:
            continue
        r = rmap.loc[pid]
        c = cmap.loc[pid] if pid in cmap.index else None
        press = g[g[press_col] == 1]
        calm = g[g[press_col] == 0]

        def split(x):
            if not len(x):
                return None
            out = {"balls": int(len(x)), "runs": int(x.bat_runs.sum()) if role == "batter"
                   else int(x.bowler_runs.sum()),
                   "impact_per_ball": float(x.impact.mean())}
            if role == "batter":
                out["strike_rate"] = float(x.bat_runs.sum() / len(x) * 100)
                out["dismissals"] = int(x.striker_out.sum())
                out["balls_per_dismissal"] = float(len(x) / max(x.striker_out.sum(), 1))
            else:
                out["economy"] = float(x.bowler_runs.sum() / len(x) * 6)
                out["wickets"] = int(x.bowler_wicket.sum())
                out["balls_per_wicket"] = float(len(x) / max(x.bowler_wicket.sum(), 1))
            return out

        by_phase = []
        for ov, gg in g.groupby("ovb", observed=True):
            pp = gg[gg[press_col] == 1]
            by_phase.append({"phase": str(ov), "balls": int(len(gg)),
                             "press_balls": int(len(pp)),
                             "impact": float(pp.impact.mean()) if len(pp) >= 10 else None})

        by_season = []
        for sy, gg in g.groupby("syear"):
            pp = gg[gg[press_col] == 1]
            by_season.append({"season": int(sy), "balls": int(len(gg)),
                              "press_balls": int(len(pp)),
                              "impact": float(pp.impact.mean()) if len(pp) >= 10 else None})

        # Signature games: biggest pressure-weighted contributions.
        ml = g.groupby("match_id").apply(lambda x: pd.Series({
            "imp": float((x.impact * x.w_press).sum()),
            "press_balls": int(x[press_col].sum()),
            "runs": float(x.bat_runs.sum()) if role == "batter" else float(x.bowler_runs.sum()),
            "wkts": float(x.striker_out.sum()) if role == "batter" else float(x.bowler_wicket.sum()),
            "balls": int(len(x)),
            "opp": x.bowling_team.iloc[0] if role == "batter" else x.batting_team.iloc[0],
            "comp": x.comp_name.iloc[0], "date": str(x.match_date.iloc[0])[:10],
            "result": x.result.iloc[0], "max_pi": float(x[pi_col].max()),
        }), include_groups=False).reset_index()
        moments = ml[ml.press_balls >= 5].nlargest(3, "imp")

        profiles.append({
            "id": int(pid), "name": str(g[name_col].iloc[0]), "role": role,
            "rank": int(r["rank"]), "superrr": float(r.superrr),
            "consensus_rank": int(c.consensus_rank) if c is not None else None,
            "mean_pct": float(c.mean_pct) if c is not None else None,
            "rank_sd": float(c.rank_sd) if c is not None and pd.notna(c.rank_sd) else None,
            "scenarios_eligible": int(c.scenarios) if c is not None else None,
            "matches": int(r.matches), "balls": int(r.balls),
            "press_balls": int(r.press_balls),
            "ipl_share": float(r.ipl_balls / max(r.balls, 1)),
            "last_season": int(r.last_season),
            "bat_pos": float(r.bat_pos) if pd.notna(r.bat_pos) else None,
            "impact_all": float(r.impact_all), "impact_press": float(r.impact_press),
            "impact_calm": float(r.impact_calm), "press_hat": float(r.press_hat),
            "clutch": float(r.clutch_raw), "consistency": float(r.pos_rate),
            "z_press": float(r.z_press), "z_clutch": float(r.z_clutch),
            "z_consistency": float(r.z_consistency),
            "pressure": split(press), "calm": split(calm),
            "by_phase": sorted(by_phase, key=lambda x: x["phase"]),
            "by_season": sorted(by_season, key=lambda x: x["season"]),
            "moments": clean(moments.drop(columns=["imp"]).assign(impact=moments.imp)),
            "teams": g[("batting_team" if role == "batter" else "bowling_team")]
                     .value_counts().head(4).index.tolist(),
        })

    profiles.sort(key=lambda p: p["consensus_rank"] or 999)
    return profiles


# --------------------------------------------------------------------------- #
def pressure_grid():
    """Precomputed chase states for the interactive calculator."""
    with open(OUT / "wp_models.pkl", "rb") as f:
        M = pickle.load(f)
    piv, m1, m2 = M["resource"], M["m1"], M["m2"]
    bb = pd.read_parquet(OUT / "balls_pressure.parquet")

    # Empirical reference distributions so the grid's pillars are scaled the
    # same way the pipeline scaled them.
    lev_sorted = np.sort(bb.leverage.to_numpy())
    med_build_bat = float(bb.p_build_bat.median())
    med_build_bowl = float(bb.p_build_bowl.median())
    start_res = float(bb.res_before.max())
    probs, _ = S3.__dict__.get("_cached_probs", (None, None)) if False else (None, None)

    balls_left = list(range(6, 121, 6))
    wkts_left = list(range(1, 11))
    needed = list(range(5, 141, 5))

    rows = []
    recs = []
    for b in balls_left:
        for w in wkts_left:
            for n in needed:
                if n > b * 6:        # beyond any realistic asking rate
                    continue
                recs.append((b, w, n))
    g = pd.DataFrame(recs, columns=["balls_left", "wkts_left", "runs_needed"])
    g["innings"] = 2
    g["balls_avail"] = 120
    g["balls_used"] = 120 - g.balls_left
    g["wkts_before"] = 10 - g.wkts_left
    g["target"] = 180
    g["score_before"] = g.target - g.runs_needed
    g["match_format"] = "T20"
    g["knock_out"] = 0
    g["res_before"] = S2.lookup_resource(piv, g.balls_left, g.wkts_left)

    g["wp_bat"] = S2.wp_batting(g, piv, m1, m2)

    # Leverage via the same outcome enumeration used in stage 2.
    oprob = outcome_probs_for_grid(bb, g)
    _, swing = S2.leverage(g, oprob, piv, m1, m2)
    g["leverage"] = swing / bb.exp_swing.mean()

    g["p_leverage"] = np.searchsorted(lev_sorted, g.leverage) / len(lev_sorted)
    g["p_scarcity"] = (1 - g.res_before / start_res).clip(0, 1)
    common = S3.W_LEV * g.p_leverage + S3.W_SCA * g.p_scarcity
    g["pi_bat"] = np.clip(100 * (common + S3.W_ADV * (1 - g.wp_bat)
                                 + S3.W_BLD * med_build_bat), 0, 100)
    g["pi_bowl"] = np.clip(100 * (common + S3.W_ADV * g.wp_bat
                                  + S3.W_BLD * med_build_bowl), 0, 100)
    cols = ["balls_left", "wkts_left", "runs_needed", "wp_bat", "leverage",
            "pi_bat", "pi_bowl"]
    return [[int(r.balls_left), int(r.wkts_left), int(r.runs_needed),
             round(float(r.wp_bat), 4), round(float(r.leverage), 3),
             round(float(r.pi_bat), 1), round(float(r.pi_bowl), 1)]
            for r in g[cols].itertuples()]


def outcome_probs_for_grid(bb, g):
    """Reuse the fitted outcome distribution, matched on the grid's state."""
    d = bb.copy()
    lab = S2.tag_outcomes(d)
    for o in S2.OUTCOMES:
        d[o] = (lab == o).astype(float)
    d["ovb"] = S2.over_bucket(d.phase_over)
    d["wl"] = d.wkts_left.clip(0, 10)
    d["rrrb"] = pd.cut(d.rrr.fillna(-1), [-2, 0, 7, 9, 11, 13, 50],
                       labels=["inn1", "<7", "7-9", "9-11", "11-13", "13+"])
    key = ["innings", "ovb", "wl"]
    tbl = d[d.innings == 2].groupby(key, observed=True)[S2.OUTCOMES].mean()

    gg = g.copy()
    gg["phase_over"] = gg.balls_used // 6 + 1
    gg["ovb"] = S2.over_bucket(gg.phase_over)
    gg["wl"] = gg.wkts_left.clip(0, 10)
    out = gg[key].merge(tbl, left_on=key, right_index=True, how="left")
    out = out[S2.OUTCOMES].fillna(d[S2.OUTCOMES].mean())
    out = out.div(out.sum(axis=1), axis=0)
    out.index = g.index
    return out


# --------------------------------------------------------------------------- #
def squad_fit(ranks_bat, ranks_bowl, cons_bat, cons_bowl):
    mp = pd.read_csv(DATA / "competition_team_player_mapping.csv")
    rr = mp[(mp.team_name == RR_TEAM) & (mp.comp_name == "IPL 2026")]
    rr_ids = set(rr.player_id)

    def mark(ranks, cons, id_col, name_col):
        r = ranks.merge(cons[[id_col, "consensus_rank", "mean_pct"]], on=id_col, how="left")
        r["at_rr"] = r[id_col].isin(rr_ids)
        return r[[id_col, name_col, "rank", "consensus_rank", "superrr", "press_hat",
                  "impact_press", "impact_calm", "clutch_raw", "pos_rate", "press_balls",
                  "matches", "ipl_balls", "balls", "last_season", "at_rr", "bat_pos"]]

    rb = mark(ranks_bat, cons_bat, "striker_id", "striker_name")
    rl = mark(ranks_bowl, cons_bowl, "bowler_id", "bowler_name")

    squad = []
    for _, p in rr.iterrows():
        b = rb[rb.striker_id == p.player_id]
        l = rl[rl.bowler_id == p.player_id]
        squad.append({
            "id": int(p.player_id), "name": p.player_name,
            "bat_rank": int(b.iloc[0]["rank"]) if len(b) else None,
            "bat_superrr": float(b.iloc[0].superrr) if len(b) else None,
            "bowl_rank": int(l.iloc[0]["rank"]) if len(l) else None,
            "bowl_superrr": float(l.iloc[0].superrr) if len(l) else None,
            "bat_pool": int(len(rb)), "bowl_pool": int(len(rl)),
        })
    squad.sort(key=lambda s: min(s["bat_rank"] or 999, s["bowl_rank"] or 999))
    return {"squad": squad,
            "targets_bat": clean(rb[~rb.at_rr].nsmallest(12, "consensus_rank")),
            "targets_bowl": clean(rl[~rl.at_rr].nsmallest(12, "consensus_rank")),
            "already_rr_bat": clean(rb[rb.at_rr].nsmallest(6, "rank")),
            "already_rr_bowl": clean(rl[rl.at_rr].nsmallest(6, "rank"))}


# --------------------------------------------------------------------------- #
def main():
    bat = pd.read_parquet(OUT / "bat_balls.parquet")
    bowl = pd.read_parquet(OUT / "bowl_balls.parquet")
    rb = pd.read_parquet(OUT / "rank_batters.parquet")
    rl = pd.read_parquet(OUT / "rank_bowlers.parquet")
    cb = pd.read_parquet(OUT / "consensus_batters.parquet")
    cl = pd.read_parquet(OUT / "consensus_bowlers.parquet")
    mm = pd.read_parquet(OUT / "matches_ctx.parquet")
    bb = pd.read_parquet(OUT / "balls_pressure.parquet")

    dmod = json.load(open(OUT / "diag_models.json"))
    dpre = json.load(open(OUT / "diag_pressure.json"))
    drat = json.load(open(OUT / "diag_ratings.json"))
    dsen = json.load(open(OUT / "diag_sensitivity.json"))

    print("writing dashboard data:")

    jdump({
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d"),
        "matches": int(mm.match_id.nunique()),
        "deliveries": int(len(bb)),
        "competitions": int(mm.comp_id.nunique()),
        "seasons": sorted(mm.season.dropna().unique().tolist()),
        "ipl_matches": int((mm.match_format == "T20").sum()),
        "t20i_matches": int((mm.match_format == "T20I").sum()),
        "players_bat_pool": int(len(rb)), "players_bowl_pool": int(len(rl)),
        "recon_exact": int((mm.recon_ok == True).sum()),
        "recon_checked": int(mm.recon_ok.notna().sum()),
        "models": {"inn1": {k: dmod["inn1"][k] for k in ("n", "log_loss", "brier", "base_rate")},
                   "inn2": {k: dmod["inn2"][k] for k in ("n", "log_loss", "brier", "base_rate")},
                   "matches_fit": dmod["n_matches_fit"]},
        "pressure_weights": {"leverage": S3.W_LEV, "adversity": S3.W_ADV,
                             "scarcity": S3.W_SCA, "buildup": S3.W_BLD,
                             "cut": S3.PRESSURE_CUT},
        "rating_params": drat["params"],
        "rating_weights": {"batting": drat["batting"]["weights"],
                           "bowling": drat["bowling"]["weights"]},
    }, "meta.json")

    jdump({"models": dmod, "pressure": dpre, "ratings": drat,
           "leverage_by_phase": clean(
               bb.assign(ovb=S2.over_bucket(bb.phase_over))
                 .groupby(["innings", "ovb"], observed=True)
                 .leverage.mean().reset_index())},
          "diagnostics.json")

    jdump({"batters": clean(rb), "bowlers": clean(rl),
           "consensus_batters": clean(cb), "consensus_bowlers": clean(cl)},
          "rankings.json")

    jdump({"table": dsen["table"], "scenarios": dsen["scenarios"],
           "batter_frequency": dsen["batter_frequency"],
           "bowler_frequency": dsen["bowler_frequency"]}, "sensitivity.json")

    jdump(player_profiles(bat, rb, cb, "striker_id", "striker_name",
                          "pi_bat", "is_press_bat", "batter"), "players_bat.json")
    jdump(player_profiles(bowl, rl, cl, "bowler_id", "bowler_name",
                          "pi_bowl", "is_press_bowl", "bowler"), "players_bowl.json")

    jdump(squad_fit(rb, rl, cb, cl), "squad.json")
    jdump(pressure_grid(), "grid.json")
    print("done.")


if __name__ == "__main__":
    main()
