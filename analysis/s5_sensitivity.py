"""Stage 5 - would a different analyst, making different reasonable choices,
pick the same players?

Every knob in the pipeline is defensible but none is uniquely correct. This
sweep re-runs the whole rating under alternative settings - a different
pressure threshold, a different view of recency, a different balance of the
four pillars - and measures how much of the top ten survives. A shortlist that
holds up across the sweep is a finding; one that moves every time is an artefact.
"""
import json

import numpy as np
import pandas as pd

from common import OUT
import s4_ratings as S

# (label, config overrides)
SCENARIOS = [
    ("baseline", {}),
    ("pressure floor 35 (wider net)", {"press_floor": 35}),
    ("pressure floor 55 (stricter)", {"press_floor": 55}),
    ("linear pressure weight", {"press_gamma": 1.0}),
    ("steep pressure weight", {"press_gamma": 2.0}),
    ("no recency decay", {"recency_decay": 1.0}),
    ("heavy recency decay", {"recency_decay": 0.60}),
    ("equal component weights", {"weight_mode": "equal"}),
    ("unadjusted component weights", {"weight_mode": "base"}),
    ("PI: leverage-heavy", {"pi_weights": (0.55, 0.20, 0.15, 0.10)}),
    ("PI: adversity-heavy", {"pi_weights": (0.30, 0.40, 0.20, 0.10)}),
    ("PI: equal pillars", {"pi_weights": (0.25, 0.25, 0.25, 0.25)}),
    ("stricter eligibility", {"min_press_balls": 140, "min_matches": 25}),
]


def spearman(a, b):
    ra, rb = pd.Series(a).rank(), pd.Series(b).rank()
    return float(np.corrcoef(ra, rb)[0, 1])


def main():
    raw = pd.read_parquet(OUT / "balls_pressure.parquet")
    results = {}
    base_rb = base_rl = None
    rows = []
    bat_frames, bowl_frames = [], []

    for label, cfg in SCENARIOS:
        rb, rl, _, _, _, _ = S.run(raw, cfg)
        bat_frames.append((label, rb))
        bowl_frames.append((label, rl))
        bat_top = rb.head(10).striker_name.tolist()
        bowl_top = rl.head(10).bowler_name.tolist()
        results[label] = {"batters": bat_top, "bowlers": bowl_top}

        if base_rb is None:
            base_rb, base_rl = rb, rl
            rows.append({"scenario": label, "bat_top10_kept": 10, "bowl_top10_kept": 10,
                         "bat_rank_corr": 1.0, "bowl_rank_corr": 1.0})
            continue

        bk = len(set(bat_top) & set(results["baseline"]["batters"]))
        lk = len(set(bowl_top) & set(results["baseline"]["bowlers"]))
        jb = base_rb[["striker_id", "composite"]].merge(
            rb[["striker_id", "composite"]], on="striker_id", suffixes=("_a", "_b"))
        jl = base_rl[["bowler_id", "composite"]].merge(
            rl[["bowler_id", "composite"]], on="bowler_id", suffixes=("_a", "_b"))
        rows.append({"scenario": label, "bat_top10_kept": bk, "bowl_top10_kept": lk,
                     "bat_rank_corr": round(spearman(jb.composite_a, jb.composite_b), 3),
                     "bowl_rank_corr": round(spearman(jl.composite_a, jl.composite_b), 3)})

    tab = pd.DataFrame(rows)

    # How often does each player appear in the top ten across all scenarios?
    def frequency(key):
        c = {}
        for v in results.values():
            for i, n in enumerate(v[key]):
                c.setdefault(n, {"appearances": 0, "best": 99, "mean_rank": []})
                c[n]["appearances"] += 1
                c[n]["best"] = min(c[n]["best"], i + 1)
                c[n]["mean_rank"].append(i + 1)
        out = [{"player": k, "top10_in": v["appearances"], "of": len(results),
                "best_rank": v["best"], "mean_rank": round(np.mean(v["mean_rank"]), 1)}
               for k, v in c.items()]
        return sorted(out, key=lambda r: (-r["top10_in"], r["mean_rank"]))

    # --- consensus ranking ----------------------------------------------------
    # Rather than trusting one parameter choice, rank each player in every
    # scenario and average their percentile position. A player has to be good
    # under most reasonable definitions of pressure to finish near the top.
    def consensus(frames, id_col, name_col):
        parts = []
        for label, d in frames:
            d = d.copy()
            d["pct"] = 1 - (d["rank"] - 1) / (len(d) - 1)
            parts.append(d[[id_col, name_col, "pct", "rank"]].assign(scenario=label))
        allp = pd.concat(parts)
        g = allp.groupby([id_col, name_col]).agg(
            scenarios=("pct", "size"), mean_pct=("pct", "mean"),
            worst_rank=("rank", "max"), best_rank=("rank", "min"),
            rank_sd=("rank", "std")).reset_index()
        g = g[g.scenarios >= len(frames) - 3]
        g = g.sort_values("mean_pct", ascending=False).reset_index(drop=True)
        g["consensus_rank"] = np.arange(1, len(g) + 1)
        return g

    cb = consensus(bat_frames, "striker_id", "striker_name")
    cl = consensus(bowl_frames, "bowler_id", "bowler_name")
    cb.to_parquet(OUT / "consensus_batters.parquet", index=False)
    cl.to_parquet(OUT / "consensus_bowlers.parquet", index=False)

    payload = {"table": tab.to_dict("records"), "scenarios": results,
               "batter_frequency": frequency("batters"),
               "bowler_frequency": frequency("bowlers"),
               "consensus_batters": cb.head(25).to_dict("records"),
               "consensus_bowlers": cl.head(25).to_dict("records")}
    with open(OUT / "diag_sensitivity.json", "w") as f:
        json.dump(payload, f, indent=2, default=float)

    print("Stability of the shortlist across alternative modelling choices")
    print(tab.to_string(index=False))
    print(f"\nmean top-10 retained - batters: {tab.bat_top10_kept[1:].mean():.1f}/10, "
          f"bowlers: {tab.bowl_top10_kept[1:].mean():.1f}/10")
    cols = ["consensus_rank", "mean_pct", "best_rank", "worst_rank", "rank_sd", "scenarios"]
    print("\n=== CONSENSUS TOP 10 BATTERS UNDER PRESSURE ===")
    print(cb.head(10)[["striker_name"] + cols].round(3).to_string(index=False))
    print("\n=== CONSENSUS TOP 10 BOWLERS UNDER PRESSURE ===")
    print(cl.head(10)[["bowler_name"] + cols].round(3).to_string(index=False))


if __name__ == "__main__":
    main()
