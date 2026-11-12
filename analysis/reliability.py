"""Split-half reliability, and the shrinkage ballast it implies.

Before trusting any per-player number we ask whether it repeats. Matches are
dealt alternately by date into two halves; a metric that measures real skill
correlates across the halves, one that measures variance does not.

Spearman-Brown converts the half-sample correlation to the reliability of the
full-length metric, and that reliability in turn fixes how hard the metric
should be shrunk: a measure that is 20% signal should be pulled four-fifths of
the way back toward its prior.
"""
import numpy as np
import pandas as pd


def deal_halves(df: pd.DataFrame) -> pd.DataFrame:
    mids = df[["match_id", "match_date"]].drop_duplicates().sort_values("match_date")
    mids["half"] = np.arange(len(mids)) % 2
    return df.merge(mids[["match_id", "half"]], on="match_id")


def _player_metrics(d: pd.DataFrame, id_col: str) -> pd.DataFrame:
    g = d.groupby(id_col).apply(lambda x: pd.Series({
        "overall": (x.impact * x.w_rec).sum() / max(x.w_rec.sum(), 1e-9),
        "press": (x.impact * x.w_press).sum() / max(x.w_press.sum(), 1e-9),
        "calm": (x.impact * x.w_calm).sum() / max(x.w_calm.sum(), 1e-9),
        "balls": len(x),
        "w_press": x.w_press.sum(),
        "w_all": x.w_rec.sum(),
    }), include_groups=False)
    g["clutch"] = g.press - g.calm
    return g


def match_consistency(d: pd.DataFrame, id_col: str, min_wp: float = 1.5) -> pd.Series:
    ml = d.groupby([id_col, "match_id"]).apply(
        lambda x: pd.Series({"wp": x.w_press.sum(), "imp": (x.impact * x.w_press).sum()}),
        include_groups=False).reset_index()
    ml = ml[ml.wp >= min_wp]
    return ml.groupby(id_col).apply(
        lambda x: pd.Series({"press_matches": len(x), "pos_rate": float((x.imp > 0).mean())}),
        include_groups=False)


def assess(df: pd.DataFrame, id_col: str, min_balls: int = 250) -> dict:
    """Full-length reliability and implied ballast for each metric."""
    d = deal_halves(df)
    a, b = (_player_metrics(d[d.half == h], id_col) for h in (0, 1))
    ca, cb = (match_consistency(d[d.half == h], id_col) for h in (0, 1))
    a, b = a.join(ca, how="left"), b.join(cb, how="left")
    j = a.join(b, lsuffix="_a", rsuffix="_b", how="inner")
    j = j[(j.balls_a >= min_balls) & (j.balls_b >= min_balls)]

    out = {"n_players": int(len(j)), "min_balls_per_half": min_balls, "metrics": {}}
    specs = [("overall", "w_all"), ("press", "w_press"),
             ("clutch", "w_press"), ("pos_rate", "press_matches")]
    for m, wcol in specs:
        xa, xb = j[f"{m}_a"], j[f"{m}_b"]
        keep = xa.notna() & xb.notna()
        if keep.sum() < 10:
            continue
        r = float(np.corrcoef(xa[keep], xb[keep])[0, 1])
        r_full = 2 * r / (1 + r) if r > -1 else 0.0
        r_full = float(np.clip(r_full, 0.01, 0.99))
        n_bar = float(pd.concat([j[f"{wcol}_a"], j[f"{wcol}_b"]]).mean() * 2)
        # Reliability r = n / (n + k)  =>  k = n (1 - r) / r
        k = n_bar * (1 - r_full) / r_full
        out["metrics"][m] = {"split_half_r": round(r, 4),
                             "full_length_r": round(r_full, 4),
                             "mean_sample": round(n_bar, 1),
                             "implied_ballast_k": round(k, 1)}
    return out


def report(res: dict, label: str):
    print(f"\n{label} - split-half reliability (n={res['n_players']} players)")
    rows = [{"metric": m, **v} for m, v in res["metrics"].items()]
    print(pd.DataFrame(rows).to_string(index=False))
