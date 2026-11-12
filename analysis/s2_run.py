"""Stage 2 driver - fit the models and attach win probability + leverage."""
import json
import pickle

import numpy as np
import pandas as pd

from common import OUT
import s2_models as S


def main():
    bb = pd.read_parquet(OUT / "balls.parquet")

    piv, fit_info = S.resource_table(bb)
    wc = S.wicket_cost_table(piv)
    m1, m2, diag, ok = S.fit_wp(bb, piv)

    probs, lvl = S.outcome_distribution(bb)
    wp, swing = S.leverage(bb, probs, piv, m1, m2)

    bb["wp_bat"] = wp                       # win prob of the side batting
    bb["exp_swing"] = swing                 # expected |dWP| from this ball
    bb["leverage"] = swing / swing.mean()   # 1.0 = an average delivery
    bb["res_before"] = S.lookup_resource(piv, bb.balls_left, bb.wkts_left)
    bb["wicket_cost"] = wc.to_numpy()[np.clip(bb.balls_left, 0, 120).astype(int),
                                      np.clip(bb.wkts_left, 0, 10).astype(int)]
    bb["outcome_level"] = lvl.to_numpy()

    bb.to_parquet(OUT / "balls_lev.parquet", index=False)
    piv.to_parquet(OUT / "resource_table.parquet")
    wc.to_parquet(OUT / "wicket_cost.parquet")
    with open(OUT / "wp_models.pkl", "wb") as f:
        pickle.dump({"m1": m1, "m2": m2, "resource": piv, "wicket_cost": wc}, f)

    diag["resource_fit"] = fit_info.round(3).to_dict("records")
    diag["leverage"] = {
        "mean_exp_swing": float(swing.mean()),
        "p90_leverage": float(np.quantile(bb.leverage, 0.90)),
        "p99_leverage": float(np.quantile(bb.leverage, 0.99)),
        "max_leverage": float(bb.leverage.max()),
        "outcome_fallback_share": {str(k): float(v) for k, v in
                                   lvl.value_counts(normalize=True).sort_index().items()},
    }
    with open(OUT / "diag_models.json", "w") as f:
        json.dump(diag, f, indent=2, default=float)

    print(f"inn2 WP : n={diag['inn2']['n']:,} logloss={diag['inn2']['log_loss']:.4f} "
          f"brier={diag['inn2']['brier']:.4f} (base {0.25:.3f})")
    print(f"inn1 WP : n={diag['inn1']['n']:,} logloss={diag['inn1']['log_loss']:.4f} "
          f"brier={diag['inn1']['brier']:.4f}")
    print(f"matches used for WP fit: {diag['n_matches_fit']} "
          f"(excluded {diag['n_matches_excluded']})")
    print("\nLeverage by phase (mean, 1.0 = average ball):")
    bb["ovb"] = S.over_bucket(bb.phase_over)
    print(bb.groupby(["innings", "ovb"], observed=True).leverage.mean().round(2).to_string())
    print("\nHighest-leverage states seen:")
    top = bb.nlargest(5, "leverage")[["match_id", "innings", "phase_over", "runs_needed",
                                      "balls_left", "wkts_left", "wp_bat", "leverage"]]
    print(top.round(2).to_string(index=False))


if __name__ == "__main__":
    main()
