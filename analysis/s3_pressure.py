"""Stage 3 - the Pressure Index.

Pressure is treated as continuous, not a binary "death overs" switch, and as
*role-relative*: the same delivery can be agony for the batter and comfort for
the bowler. Four pillars, each scaled to 0-1, combine into PI on 0-100:

  LEVERAGE  (40%)  how much this ball can swing the result       -> stage 2
  ADVERSITY (25%)  how badly your own side is placed right now
  SCARCITY  (20%)  how much batting resource has already gone
  BUILD-UP  (15%)  the squeeze applied over the preceding 12 balls

A knockout multiplier lifts elimination games. The index is then validated by
checking that scoring genuinely degrades as PI rises - if it did not, the
definition would be measuring something other than pressure.
"""
import json

import numpy as np
import pandas as pd

from common import OUT

W_LEV, W_ADV, W_SCA, W_BLD = 0.40, 0.25, 0.20, 0.15
KNOCKOUT_MULT = 1.08
PRESSURE_CUT = 65          # PI at or above this counts as a pressure ball


def ecdf_rank(x: pd.Series) -> np.ndarray:
    """Percentile position of each value within the sample (0-1)."""
    return x.rank(method="average", pct=True).to_numpy()


def build_up(bb: pd.DataFrame):
    """Pressure accumulated over the previous 12 legal deliveries.

    This pillar is asymmetric, and that matters. A run of dots and wickets
    strangles the *batter* - the scoreboard stops and the required rate climbs
    on its own - but for the bowler those same balls are pressure he is
    applying, not absorbing. The bowler's build-up is the mirror image: runs
    and boundaries flowing off the previous overs.
    """
    d = bb[["match_id", "innings", "legal", "total_runs", "is_wicket",
            "is_four", "is_six"]].copy()
    d["dot"] = ((d.total_runs == 0) & (d.legal == 1)).astype(float)
    d["wk"] = d.is_wicket.astype(float)
    d["bdry"] = (d.is_four | d.is_six).astype(float)
    g = d.groupby(["match_id", "innings"], sort=False)

    def roll(col, fn):
        # shift(1) so a ball is never scored using its own outcome.
        return g[col].transform(lambda s: getattr(s.shift(1).rolling(12, min_periods=4), fn)())

    dots = roll("dot", "mean").fillna(0.40)
    wkts = roll("wk", "sum").fillna(0.0)
    runs = roll("total_runs", "mean").fillna(1.25)
    bdry = roll("bdry", "mean").fillna(0.16)

    bat = dots + 0.25 * wkts                 # strangled
    bowl = runs / 1.25 + 1.5 * bdry          # being taken apart
    return bat.to_numpy(), bowl.to_numpy()


def add_pressure(bb: pd.DataFrame) -> pd.DataFrame:
    bb = bb.copy()

    # --- pillar 1: leverage ---------------------------------------------------
    # Leverage is extremely long-tailed (a last-ball thriller is 40x an average
    # delivery), so rank rather than scale it.
    bb["p_leverage"] = ecdf_rank(bb.leverage)

    # --- pillar 2: adversity (role-relative) ---------------------------------
    bb["p_adv_bat"] = 1.0 - bb.wp_bat
    bb["p_adv_bowl"] = bb.wp_bat

    # --- pillar 3: scarcity ---------------------------------------------------
    # Share of the innings' batting resource already consumed, straight off the
    # fitted DL surface, so balls and wickets are priced on one scale.
    start = bb.res_before.max()
    bb["p_scarcity"] = (1.0 - bb.res_before / start).clip(0, 1)

    # --- pillar 4: build-up (role-specific) -----------------------------------
    raw_bat, raw_bowl = build_up(bb)
    bb["build_raw_bat"], bb["build_raw_bowl"] = raw_bat, raw_bowl
    bb["p_build_bat"] = ecdf_rank(bb.build_raw_bat)
    bb["p_build_bowl"] = ecdf_rank(bb.build_raw_bowl)

    mult = np.where(bb.knock_out == 1, KNOCKOUT_MULT, 1.0)
    common = W_LEV * bb.p_leverage + W_SCA * bb.p_scarcity
    bb["pi_bat"] = np.clip(
        100 * (common + W_ADV * bb.p_adv_bat + W_BLD * bb.p_build_bat) * mult, 0, 100)
    bb["pi_bowl"] = np.clip(
        100 * (common + W_ADV * bb.p_adv_bowl + W_BLD * bb.p_build_bowl) * mult, 0, 100)

    bb["is_press_bat"] = (bb.pi_bat >= PRESSURE_CUT).astype(int)
    bb["is_press_bowl"] = (bb.pi_bowl >= PRESSURE_CUT).astype(int)
    return bb


# --------------------------------------------------------------------------- #
# validation
# --------------------------------------------------------------------------- #
def validate(bb: pd.DataFrame) -> dict:
    """Does the index actually separate hard situations from ordinary ones?"""
    out = {}

    def profile(d, col, label):
        d = d.copy()
        d["band"] = pd.cut(d[col], [0, 20, 35, 50, 65, 80, 100],
                           labels=["0-20", "20-35", "35-50", "50-65", "65-80", "80-100"])
        g = d.groupby("band", observed=True).agg(
            balls=("legal", "sum"),
            runs=("total_runs", "sum"),
            dots=("is_dot", "sum"),
            fours=("is_four", "sum"),
            sixes=("is_six", "sum"),
            wkts=("is_wicket", "sum"),
        ).reset_index()
        g["run_rate"] = g.runs / g.balls * 6
        g["dot_pct"] = g.dots / g.balls * 100
        g["bdry_pct"] = (g.fours + g.sixes) / g.balls * 100
        g["wkt_per_100"] = g.wkts / g.balls * 100
        # The decisive one. Run rate alone is misleading because high-pressure
        # balls cluster at the death, where everyone swings; what pressure
        # really costs is survival, so price runs against dismissals.
        g["runs_per_dismissal"] = g.runs / g.wkts
        g["band"] = g.band.astype(str)
        out[label] = g.round(3).to_dict("records")
        return g

    bb = bb.copy()
    bb["is_dot"] = ((bb.total_runs == 0) & (bb.legal == 1)).astype(int)
    gb = profile(bb, "pi_bat", "batting_by_pi")
    profile(bb, "pi_bowl", "bowling_by_pi")

    # Monotonicity checks across bands.
    rpd = gb.runs_per_dismissal.to_numpy()
    wk = gb.wkt_per_100.to_numpy()
    out["monotonic_rpd_down"] = bool(np.all(np.diff(rpd) < 0))
    out["monotonic_rpd_down_top4"] = bool(np.all(np.diff(rpd[2:]) < 0))
    out["rpd_drop_pct"] = float((rpd[0] - rpd[-1]) / rpd[0] * 100)
    out["wkt_rate_rise_pct"] = float((wk[-1] - wk[0]) / wk[0] * 100)
    out["runrate_change_pct"] = float((gb.run_rate.to_numpy()[-1] - gb.run_rate.to_numpy()[0])
                                      / gb.run_rate.to_numpy()[0] * 100)

    # --- phase-controlled check ----------------------------------------------
    # High-PI balls cluster in the death overs, where everyone concedes more and
    # loses more wickets. To show PI carries information beyond "which over is
    # it", compare the top and bottom PI terciles *within* each phase.
    def within_phase(col, label):
        d = bb[bb.legal == 1].copy()
        d["ovb"] = pd.cut(d.phase_over, [0, 6, 11, 15, 17, 20],
                          labels=["1-6", "7-11", "12-15", "16-17", "18-20"])
        d["terc"] = d.groupby("ovb", observed=True)[col].transform(
            lambda s: pd.qcut(s, 3, labels=["low", "mid", "high"], duplicates="drop"))
        g = (d[d.terc.isin(["low", "high"])]
             .groupby(["ovb", "terc"], observed=True)
             .agg(balls=("legal", "sum"), runs=("total_runs", "sum"),
                  wkts=("is_wicket", "sum")).reset_index())
        g["run_rate"] = g.runs / g.balls * 6
        g["wkt_per_100"] = g.wkts / g.balls * 100
        g["runs_per_dismissal"] = g.runs / g.wkts
        g["ovb"] = g.ovb.astype(str)
        g["terc"] = g.terc.astype(str)
        out[label] = g.round(3).to_dict("records")
        return g

    wb = within_phase("pi_bat", "batting_within_phase")
    wl = within_phase("pi_bowl", "bowling_within_phase")
    piv_b = wb.pivot(index="ovb", columns="terc", values="runs_per_dismissal")
    out["within_phase_rpd_gap"] = {k: float(v) for k, v in
                                   ((piv_b["high"] - piv_b["low"]) / piv_b["low"] * 100).items()}
    piv_l = wl.pivot(index="ovb", columns="terc", values="run_rate")
    out["within_phase_economy_gap"] = {k: float(v) for k, v in
                                       ((piv_l["high"] - piv_l["low"])).items()}

    # --- robustness: does the signal depend on any one pillar? ----------------
    # Build-up is the pillar most at risk of flattering the result, because
    # recent scoring autocorrelates with the current ball. Strip it out (and
    # then strip everything except leverage) and re-measure the same gap.
    def gap_for(series, metric="runs_per_dismissal"):
        d = bb[bb.legal == 1].copy()
        d["_pi"] = series[bb.legal == 1].to_numpy()
        d["ovb"] = pd.cut(d.phase_over, [0, 6, 11, 15, 17, 20],
                          labels=["1-6", "7-11", "12-15", "16-17", "18-20"])
        d["terc"] = d.groupby("ovb", observed=True)._pi.transform(
            lambda s: pd.qcut(s, 3, labels=["low", "mid", "high"], duplicates="drop"))
        g = (d[d.terc.isin(["low", "high"])].groupby(["ovb", "terc"], observed=True)
             .agg(balls=("legal", "sum"), runs=("total_runs", "sum"),
                  wkts=("is_wicket", "sum")))
        g["runs_per_dismissal"] = g.runs / g.wkts
        g["run_rate"] = g.runs / g.balls * 6
        p = g[metric].unstack()
        return {str(k): round(float(v), 1)
                for k, v in ((p["high"] - p["low"]) / p["low"] * 100).items()}

    no_build = (W_LEV * bb.p_leverage + W_SCA * bb.p_scarcity) / (W_LEV + W_SCA) \
        * (1 - W_ADV) * 100 + W_ADV * bb.p_adv_bat * 100
    out["robustness"] = {
        "full_index": gap_for(bb.pi_bat),
        "without_buildup": gap_for(no_build),
        "leverage_only": gap_for(bb.p_leverage * 100),
        "note": ("Percentage change in runs per dismissal, top vs bottom PI tercile, "
                 "within phase. Leverage alone separates almost nothing outside the "
                 "death overs, which is why the index is a composite."),
    }

    # Correlations on legal deliveries only.
    leg = bb[bb.legal == 1]
    out["corr_pi_runs"] = float(np.corrcoef(leg.pi_bat, leg.total_runs)[0, 1])
    out["corr_pi_wicket"] = float(np.corrcoef(leg.pi_bat, leg.is_wicket.astype(float))[0, 1])

    # Share of deliveries flagged as pressure, and how that moves with the cut.
    out["pressure_share_bat"] = float(bb.is_press_bat.mean())
    out["pressure_share_bowl"] = float(bb.is_press_bowl.mean())
    out["cut_sensitivity"] = [
        {"cut": c, "share_bat": float((bb.pi_bat >= c).mean()),
         "share_bowl": float((bb.pi_bowl >= c).mean())}
        for c in (55, 60, 65, 70, 75)
    ]
    out["pi_distribution"] = [
        {"pi": int(lo), "count": int(((bb.pi_bat >= lo) & (bb.pi_bat < lo + 5)).sum())}
        for lo in range(0, 100, 5)
    ]
    # Where the pressure balls actually come from.
    pb = bb[bb.is_press_bat == 1]
    out["pressure_by_innings"] = (pb.groupby("innings").size() / len(pb)).round(4).to_dict()
    out["pressure_by_over"] = (pb.groupby("phase_over").size() / len(pb)).round(4).to_dict()
    return out


def main():
    bb = pd.read_parquet(OUT / "balls_lev.parquet")
    bb = add_pressure(bb)
    bb.to_parquet(OUT / "balls_pressure.parquet", index=False)

    v = validate(bb)
    with open(OUT / "diag_pressure.json", "w") as f:
        json.dump(v, f, indent=2, default=float)

    print("Batting outcomes by Pressure Index band")
    print(pd.DataFrame(v["batting_by_pi"])[
        ["band", "balls", "run_rate", "dot_pct", "bdry_pct", "wkt_per_100",
         "runs_per_dismissal"]
    ].round(2).to_string(index=False))
    print(f"\nruns per dismissal, monotone falling : {v['monotonic_rpd_down']} "
          f"(top four bands: {v['monotonic_rpd_down_top4']})")
    print(f"runs per dismissal, low -> high PI   : -{v['rpd_drop_pct']:.1f}%")
    print(f"dismissal rate rise                  : +{v['wkt_rate_rise_pct']:.1f}%")
    print(f"run rate change                      : {v['runrate_change_pct']:+.1f}%")
    print(f"pressure balls (PI>={PRESSURE_CUT})               : "
          f"{v['pressure_share_bat']:.1%} batting / {v['pressure_share_bowl']:.1%} bowling")

    print("\nBowling outcomes by Pressure Index band")
    print(pd.DataFrame(v["bowling_by_pi"])[
        ["band", "balls", "run_rate", "wkt_per_100", "runs_per_dismissal"]
    ].round(2).to_string(index=False))

    print("\nPhase-controlled: top vs bottom PI tercile within each phase")
    wb = pd.DataFrame(v["batting_within_phase"]).pivot(
        index="ovb", columns="terc", values="runs_per_dismissal")
    wb["gap_%"] = (wb["high"] - wb["low"]) / wb["low"] * 100
    print("  batting, runs per dismissal:")
    print(wb.round(1).to_string())
    wl = pd.DataFrame(v["bowling_within_phase"]).pivot(
        index="ovb", columns="terc", values="run_rate")
    wl["gap"] = wl["high"] - wl["low"]
    print("  bowling, runs per over conceded:")
    print(wl.round(2).to_string())

    print("\nRobustness - runs/dismissal gap (%) by index variant:")
    print(pd.DataFrame(v["robustness"]).drop(index=[], errors="ignore")
          .loc[["1-6", "7-11", "12-15", "16-17", "18-20"],
               ["full_index", "without_buildup", "leverage_only"]].to_string())


if __name__ == "__main__":
    main()
