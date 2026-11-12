"""Small self-contained modelling utilities (no sklearn dependency).

Keeping these hand-rolled means the whole pipeline runs on numpy/pandas alone
and every coefficient is inspectable.
"""
import numpy as np
import pandas as pd


class Logit:
    """L2-regularised logistic regression fitted by Newton-Raphson (IRLS)."""

    def __init__(self, l2: float = 1.0, max_iter: int = 60, tol: float = 1e-7):
        self.l2, self.max_iter, self.tol = l2, max_iter, tol
        self.beta = None
        self.mu = None
        self.sd = None
        self.names = None

    def _prep(self, X, fit=False):
        X = np.asarray(X, dtype=float)
        if fit:
            self.mu = X.mean(0)
            self.sd = X.std(0)
            self.sd[self.sd == 0] = 1.0
        Z = (X - self.mu) / self.sd
        return np.hstack([np.ones((len(Z), 1)), Z])

    def fit(self, X, y, names=None, w=None):
        self.names = names
        A = self._prep(X, fit=True)
        y = np.asarray(y, dtype=float)
        w = np.ones(len(y)) if w is None else np.asarray(w, dtype=float)
        b = np.zeros(A.shape[1])
        pen = np.eye(A.shape[1]) * self.l2
        pen[0, 0] = 0.0                       # never penalise the intercept
        for _ in range(self.max_iter):
            p = 1.0 / (1.0 + np.exp(-np.clip(A @ b, -30, 30)))
            W = w * np.clip(p * (1 - p), 1e-9, None)
            grad = A.T @ (w * (y - p)) - pen @ b
            H = (A.T * W) @ A + pen
            step = np.linalg.solve(H, grad)
            b += step
            if np.max(np.abs(step)) < self.tol:
                break
        self.beta = b
        return self

    def predict(self, X):
        A = self._prep(np.asarray(X, dtype=float))
        return 1.0 / (1.0 + np.exp(-np.clip(A @ self.beta, -30, 30)))

    def coef_table(self):
        names = self.names or [f"x{i}" for i in range(len(self.beta) - 1)]
        return pd.DataFrame({"term": ["intercept"] + list(names),
                             "coef_std": self.beta})


def log_loss(y, p):
    p = np.clip(p, 1e-9, 1 - 1e-9)
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))


def brier(y, p):
    return float(np.mean((np.asarray(y, float) - p) ** 2))


def calibration(y, p, bins=10):
    """Reliability table: predicted vs observed, for model diagnostics."""
    df = pd.DataFrame({"y": np.asarray(y, float), "p": p})
    df["bin"] = pd.cut(df.p, np.linspace(0, 1, bins + 1), include_lowest=True)
    g = df.groupby("bin", observed=True).agg(n=("y", "size"), pred=("p", "mean"),
                                             obs=("y", "mean")).reset_index()
    g["bin"] = g["bin"].astype(str)
    return g


def hierarchical_mean(df, value_cols, key_levels, min_n):
    """Empirical means over progressively coarser keys.

    key_levels is a list of column-lists, finest first. A cell is taken from the
    finest key that has at least `min_n` observations, else it falls back.
    Returns a frame aligned to df's index with one column per value_col.
    """
    out = pd.DataFrame(index=df.index, columns=value_cols, dtype=float)
    filled = pd.Series(False, index=df.index)
    levels_used = pd.Series(len(key_levels), index=df.index)
    for lvl, keys in enumerate(key_levels):
        g = df.groupby(keys, observed=True)[value_cols].agg(["mean", "size"])
        counts = g[(value_cols[0], "size")]
        means = g.xs("mean", axis=1, level=1)
        ok = counts[counts >= min_n].index
        means = means.loc[means.index.isin(ok)]
        joined = df[keys].merge(means, left_on=keys, right_index=True, how="left")
        for c in value_cols:
            take = (~filled) & joined[c].notna()
            out.loc[take, c] = joined.loc[take, c]
        newly = (~filled) & joined[value_cols[0]].notna()
        levels_used[newly] = lvl
        filled = filled | newly
    # Anything still unfilled gets the global mean.
    for c in value_cols:
        out[c] = out[c].fillna(df[c].mean())
    return out, levels_used
