"""Stage 1 - rebuild the live match state behind every delivery.

The ball-by-ball file tells us what happened on a ball but not the situation the
player walked into. Everything downstream (pressure, expected runs, leverage)
keys off the *pre-ball* state, so we reconstruct it here and sanity-check the
reconstruction against the official result strings.
"""
import re

import numpy as np
import pandas as pd

from common import DATA, OUT, ILLEGAL_EXTRAS, DEV_COMP_PATTERNS, TIER1, load_raw


def to_bool(s):
    return s.astype(str).str.lower().isin({"true", "1"})


def build():
    bb, matches, comps, teams, mapping = load_raw()

    bb = bb[bb.innings.isin([1, 2])].copy()  # drop super-overs
    bb = bb.sort_values(["match_id", "innings", "innings_ball_num"]).reset_index(drop=True)

    for c in ("extras1_runs", "extras_2_runs", "runs"):
        bb[c] = pd.to_numeric(bb[c], errors="coerce").fillna(0)
    bb["is_wicket"] = to_bool(bb.is_wicket)
    bb["is_four"] = to_bool(bb.is_four)
    bb["is_six"] = to_bool(bb.is_six)

    bb["extras_runs"] = bb.extras1_runs + bb.extras_2_runs
    bb["total_runs"] = bb.runs + bb.extras_runs
    bb["legal"] = (~bb.extras_type.isin(ILLEGAL_EXTRAS)).astype(int)

    # A wicket is credited to the bowler for everything except run-outs,
    # retirements and obstruction.
    bowler_credit = {"Caught", "Bowled", "LBW", "Stump", "Hit Wicket"}
    bb["bowler_wicket"] = (bb.is_wicket & bb.dismissal_type.isin(bowler_credit)).astype(int)
    # Runs charged to the bowler exclude byes/leg-byes.
    off_bowler = ~bb.extras_type.isin({"byes", "legbyes", "Penalty"})
    bb["bowler_runs"] = np.where(off_bowler, bb.total_runs, bb.runs)

    g = bb.groupby(["match_id", "innings"], sort=False)
    bb["score_before"] = g.total_runs.cumsum() - bb.total_runs
    bb["wkts_before"] = g.is_wicket.cumsum().astype(int) - bb.is_wicket.astype(int)

    # Anchor the ball count to the official over number rather than a running
    # cumulative sum: any single mis-tagged extra then costs one ball inside one
    # over instead of shifting every subsequent state in the innings.
    go = bb.groupby(["match_id", "innings", "overid"], sort=False)
    legal_in_over = go.legal.cumsum() - bb.legal
    bb["balls_used"] = (bb.overid - 1) * 6 + legal_in_over.clip(upper=5)

    # ---- innings and match level context -------------------------------------
    inn = g.agg(inn_runs=("total_runs", "sum"),
                inn_wkts=("is_wicket", "sum"),
                inn_balls=("legal", "sum")).reset_index()
    inn_tot = inn.pivot(index="match_id", columns="innings",
                        values=["inn_runs", "inn_wkts", "inn_balls"])
    inn_tot.columns = [f"{a}_{b}" for a, b in inn_tot.columns]
    inn_tot = inn_tot.reset_index()

    mm = matches.merge(comps, on="comp_id", how="left").merge(inn_tot, on="match_id", how="inner")

    for c in ("first_inn_revised_overs", "second_inn_revised_overs", "revised_target"):
        mm[c] = pd.to_numeric(mm[c], errors="coerce")
    mm["overs1"] = mm.first_inn_revised_overs.where(mm.first_inn_revised_overs > 0, 20.0)
    mm["overs2"] = mm.second_inn_revised_overs.where(mm.second_inn_revised_overs > 0, mm.overs1)
    mm["target"] = mm.revised_target.where(mm.revised_target > 0, mm.inn_runs_1 + 1)

    mm["is_dev_comp"] = mm.comp_name.str.contains("|".join(DEV_COMP_PATTERNS), case=False, na=False)
    mm["knock_out"] = pd.to_numeric(mm.knock_out, errors="coerce").fillna(0).astype(int)

    # Which side batted first? Innings 1's batting team, taken from the data.
    bat1 = bb[bb.innings == 1].groupby("match_id").batting_team_id.first().rename("bat_first_id")
    mm = mm.merge(bat1, on="match_id", how="left")
    mm["bowl_first_id"] = np.where(mm.bat_first_id == mm.home_team_id,
                                   mm.away_team_id, mm.home_team_id)

    # ---- integrity check: does our reconstruction agree with the result string?
    mm = check_results(mm)

    # ---- attach context to every ball ----------------------------------------
    ctx = mm[["match_id", "comp_id", "comp_name", "match_format", "season", "match_date",
              "venue_country", "knock_out", "is_dev_comp", "overs1", "overs2", "target",
              "inn_runs_1", "win_team_id", "result", "recon_ok"]]
    bb = bb.merge(ctx, on="match_id", how="inner")

    bb["overs_avail"] = np.where(bb.innings == 1, bb.overs1, bb.overs2)
    bb["balls_avail"] = (bb.overs_avail * 6).round().astype(int)
    bb["balls_left"] = (bb.balls_avail - bb.balls_used).clip(lower=0)
    bb["wkts_left"] = (10 - bb.wkts_before).clip(lower=0)
    bb["phase_over"] = bb.balls_used // 6 + 1

    # Chase arithmetic (innings 2 only).
    bb["runs_needed"] = np.where(bb.innings == 2, bb.target - bb.score_before, np.nan)
    with np.errstate(divide="ignore", invalid="ignore"):
        bb["rrr"] = np.where((bb.innings == 2) & (bb.balls_left > 0),
                             bb.runs_needed * 6.0 / bb.balls_left, np.nan)
        bb["crr"] = np.where(bb.balls_used > 0, bb.score_before * 6.0 / bb.balls_used, np.nan)

    # Opposition quality, used later to stop flat-track/minnow bullying inflating ratings.
    name_by_id = pd.concat([
        matches[["home_team_id", "home_team"]].rename(columns={"home_team_id": "tid", "home_team": "tname"}),
        matches[["away_team_id", "away_team"]].rename(columns={"away_team_id": "tid", "away_team": "tname"}),
    ]).drop_duplicates("tid").set_index("tid").tname
    bb["batting_team"] = bb.batting_team_id.map(name_by_id)
    bb["bowling_team"] = bb.bowling_team_id.map(name_by_id)

    bb["ball_uid"] = (bb.match_id.astype(str) + "_" + bb.innings.astype(str) + "_"
                      + bb.innings_ball_num.astype(str))

    bb.to_parquet(OUT / "balls.parquet", index=False)
    mm.to_parquet(OUT / "matches_ctx.parquet", index=False)
    report(bb, mm)
    return bb, mm


RUNS_RE = re.compile(r"Won by (\d+) Run", re.I)
WKTS_RE = re.compile(r"Won by (\d+) Wicket", re.I)


def check_results(mm: pd.DataFrame) -> pd.DataFrame:
    """Verify rebuilt innings totals reproduce the official margin."""
    ok = []
    for r in mm.itertuples():
        res = str(r.result or "")
        r1, r2 = r.inn_runs_1, r.inn_runs_2
        if pd.isna(r1) or pd.isna(r2):
            ok.append(False)
            continue
        m_runs, m_wkts = RUNS_RE.search(res), WKTS_RE.search(res)
        if m_runs:                      # team batting first defended
            ok.append(abs((r1 - r2) - int(m_runs.group(1))) <= 0)
        elif m_wkts:                    # chase completed
            ok.append(abs((10 - r.inn_wkts_2) - int(m_wkts.group(1))) <= 0 and r2 >= r.target)
        else:                           # tie / no-result / DLS wording
            ok.append(np.nan)
        continue
    mm["recon_ok"] = pd.Series(ok, index=mm.index).astype("object")
    return mm


def report(bb, mm):
    chk = mm.recon_ok.dropna()
    print(f"matches with ball data      : {mm.match_id.nunique()}")
    print(f"result-string reconstruction: {int((chk == True).sum())}/{len(chk)} exact "
          f"({(chk == True).mean():.1%}); {mm.recon_ok.isna().sum()} ties/no-results skipped")
    print(f"deliveries (innings 1-2)    : {len(bb):,}")
    bad = mm[mm.recon_ok == False]
    if len(bad):
        print("\nmismatches (first 8):")
        print(bad[["match_id", "comp_name", "inn_runs_1", "inn_runs_2", "inn_wkts_2",
                   "target", "result"]].head(8).to_string(index=False))


if __name__ == "__main__":
    build()
