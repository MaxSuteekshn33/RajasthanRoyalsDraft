"""Stage 2 - the statistical backbone.

Four objects are produced, in dependency order:

  1. Resource table  R(balls_left, wickets_left) -> expected runs still to come.
  2. Wicket cost     WC(balls_left, wickets_left) = R(w) - R(w-1), in runs.
  3. Win-probability models, one per innings, fitted by IRLS logistic.
  4. Leverage        LI(state) = expected |swing in win probability| from one
                     ball, obtained by enumerating ball outcomes against their
                     state-conditional probabilities.

Leverage is deliberately built only from *objective* match state so that the
Pressure Index in stage 3 can use it without circularity.
"""
import json

import numpy as np
import pandas as pd

from common import OUT
from model_lib import Logit, log_loss, brier, calibration, hierarchical_mean

OUTCOMES = ["o0", "o1", "o2", "o3", "o4", "o6", "ow", "ox"]
OUT_RUNS = {"o0": 0, "o1": 1, "o2": 2, "o3": 3, "o4": 4, "o6": 6, "ow": 0, "ox": 1}


# --------------------------------------------------------------------------- #
# universe
# --------------------------------------------------------------------------- #
def clean_match_universe(bb: pd.DataFrame) -> pd.Series:
    """Matches whose outcome can be trusted for fitting win-probability."""
    mm = bb.groupby("match_id").agg(
        innings_seen=("innings", "nunique"),
        win_team_id=("win_team_id", "first"),
        result=("result", "first"),
    )
    end2 = (bb[bb.innings == 2].sort_values("innings_ball_num")
            .groupby("match_id")
            .agg(sc=("score_before", "last"), tr=("total_runs", "last"),
                 wk=("wkts_before", "last"), iw=("is_wicket", "last"),
                 bu=("balls_used", "last"), lg=("legal", "last"),
                 ba=("balls_avail", "last"), tgt=("target", "last")))
    end2["final"] = end2.sc + end2.tr
    end2["wkts"] = end2.wk + end2.iw.astype(int)
    end2["balls"] = end2.bu + end2.lg
    # A genuinely finished chase ends one of three ways.
    end2["resolved"] = ((end2.final >= end2.tgt) | (end2.wkts >= 10)
                        | (end2.balls >= end2.ba))
    mm = mm.join(end2[["resolved"]])
    bad_result = mm.result.str.contains("Abandon|No Result", case=False, na=True)
    ok = (mm.innings_seen == 2) & mm.win_team_id.notna() & mm.resolved.fillna(False) & ~bad_result
    return ok


# --------------------------------------------------------------------------- #
# 1-2. resource + wicket-cost tables
# --------------------------------------------------------------------------- #
def _fit_dl_curve(b, y, n):
    """Weighted least-squares fit of R(b) = Z * (1 - exp(-lam * b / Z)).

    This is the Duckworth-Lewis resource form: lam is the scoring rate per ball
    at the start, Z the asymptotic ceiling. Fitted by refined grid search so the
    pipeline stays on numpy alone.
    """
    zs = np.linspace(5, 320, 180)
    ls = np.linspace(0.05, 3.0, 180)
    best = (np.inf, zs[0], ls[0])
    for _ in range(3):
        Z = zs[:, None, None]
        L = ls[None, :, None]
        pred = Z * (1 - np.exp(-L * b[None, None, :] / Z))
        sse = (n[None, None, :] * (pred - y[None, None, :]) ** 2).sum(axis=2)
        i, j = np.unravel_index(np.argmin(sse), sse.shape)
        best = (sse[i, j], zs[i], ls[j])
        zs = np.linspace(max(1.0, zs[i] - (zs[1] - zs[0]) * 2), zs[i] + (zs[1] - zs[0]) * 2, 60)
        ls = np.linspace(max(0.01, ls[j] - (ls[1] - ls[0]) * 2), ls[j] + (ls[1] - ls[0]) * 2, 60)
    return best[1], best[2]


def resource_table(bb: pd.DataFrame, min_cell: int = 15):
    """Expected further runs from (balls_left, wickets_left).

    Fitted on first innings only: those are unconstrained by a target, so they
    describe a side's natural scoring capacity rather than chase behaviour.
    Sparse (balls_left, wickets_left) corners are never observed in real games,
    so rather than smoothing noise we fit a parametric DL-style curve per
    wicket column, which extrapolates monotonically by construction.
    """
    f = bb[(bb.innings == 1) & (bb.balls_avail == 120)].copy()
    final = (f.groupby("match_id")
               .apply(lambda d: d.score_before.iloc[-1] + d.total_runs.iloc[-1],
                      include_groups=False).rename("inn_final"))
    f = f.join(final, on="match_id")
    f["remaining"] = f.inn_final - f.score_before

    grid = (f.groupby(["balls_left", "wkts_left"])
              .agg(r=("remaining", "mean"), n=("remaining", "size")).reset_index())

    params = {}
    for w in range(1, 11):
        cell = grid[(grid.wkts_left == w) & (grid.n >= min_cell)]
        if len(cell) < 6:                      # too sparse to fit on its own
            params[w] = None
            continue
        params[w] = _fit_dl_curve(cell.balls_left.to_numpy(float),
                                  cell.r.to_numpy(float), cell.n.to_numpy(float))

    # Fill unfittable wicket columns by scaling the nearest fitted one down.
    fitted = [w for w in range(1, 11) if params[w]]
    for w in range(1, 11):
        if params[w] is None:
            ref = min(fitted, key=lambda x: abs(x - w))
            Z, L = params[ref]
            k = w / ref
            params[w] = (Z * k, L * k)

    Zs = np.array([params[w][0] for w in range(1, 11)])
    Ls = np.array([params[w][1] for w in range(1, 11)])
    Zs = np.maximum.accumulate(Zs)             # more wickets in hand is never worse
    Ls = np.maximum.accumulate(Ls)

    b = np.arange(0, 121, dtype=float)[:, None]
    curve = Zs[None, :] * (1 - np.exp(-Ls[None, :] * b / Zs[None, :]))
    curve = np.hstack([np.zeros((121, 1)), curve])  # column 0 = all out

    # Trust the observed mean where a cell is well populated, the curve where it
    # is not. Weight crosses 50/50 at 30 observations.
    emp = np.full_like(curve, np.nan)
    cnt = np.zeros_like(curve)
    for r in grid.itertuples():
        if r.balls_left <= 120:
            emp[int(r.balls_left), int(r.wkts_left)] = r.r
            cnt[int(r.balls_left), int(r.wkts_left)] = r.n
    wgt = cnt / (cnt + 30.0)
    arr = np.where(np.isnan(emp), curve, wgt * np.nan_to_num(emp) + (1 - wgt) * curve)

    arr = np.maximum.accumulate(arr, axis=0)   # monotone in balls remaining
    arr = np.maximum.accumulate(arr, axis=1)   # monotone in wickets in hand
    arr[0, :] = 0.0
    arr[:, 0] = 0.0
    piv = pd.DataFrame(arr, index=pd.Index(np.arange(0, 121), name="balls_left"),
                       columns=pd.Index(np.arange(0, 11), name="wkts_left"))
    fit_info = pd.DataFrame({"wkts_left": range(1, 11), "Z": Zs, "lambda": Ls})
    return piv, fit_info


def lookup_resource(piv, balls_left, wkts_left):
    b = np.clip(np.asarray(balls_left, int), 0, 120)
    w = np.clip(np.asarray(wkts_left, int), 0, 10)
    return piv.to_numpy()[b, w]


def wicket_cost_table(piv: pd.DataFrame) -> pd.DataFrame:
    """Runs-equivalent price of a wicket: the batting resource it destroys."""
    arr = piv.to_numpy()
    wc = np.zeros_like(arr)
    wc[:, 1:] = arr[:, 1:] - arr[:, :-1]
    wc[:, 0] = wc[:, 1]
    df = pd.DataFrame(wc, index=piv.index, columns=piv.columns)
    # Differencing amplifies residual noise; the true surface varies smoothly
    # with balls remaining, so average over a 15-ball window.
    df = df.rolling(15, center=True, min_periods=1).mean()
    return df.clip(lower=2.0)


# --------------------------------------------------------------------------- #
# 3. win probability
# --------------------------------------------------------------------------- #
def chase_features(d, piv):
    r = np.clip(d.runs_needed.to_numpy(float), 0, None)
    b = np.clip(d.balls_left.to_numpy(float), 1, None)
    w = d.wkts_left.to_numpy(float)
    res = np.clip(lookup_resource(piv, d.balls_left, d.wkts_left), 1.0, None)
    rrr = np.clip(r * 6.0 / b, 0, 36)
    ask = np.clip(r / res, 0, 6)              # required runs vs runs the state can supply
    X = np.column_stack([
        ask, np.log1p(ask), rrr, w, np.log1p(b),
        rrr * (10 - w) / 10.0,                # asking rate bites harder with fewer wickets
        d.target.to_numpy(float) * 6.0 / np.clip(d.balls_avail.to_numpy(float), 1, None),
        (d.match_format == "T20I").astype(float).to_numpy(),
    ])
    names = ["ask_ratio", "log_ask", "rrr", "wkts_left", "log_balls_left",
             "rrr_x_wkts_lost", "target_rate", "is_t20i"]
    return X, names


def inn1_features(d, piv):
    res = lookup_resource(piv, d.balls_left, d.wkts_left)
    proj = d.score_before.to_numpy(float) + res
    bu = np.clip(d.balls_used.to_numpy(float), 1, None)
    X = np.column_stack([
        proj, proj ** 2 / 100.0,
        d.wkts_left.to_numpy(float),
        np.log1p(d.balls_left.to_numpy(float)),
        d.score_before.to_numpy(float) * 6.0 / bu,
        (d.match_format == "T20I").astype(float).to_numpy(),
    ])
    names = ["proj_score", "proj_score_sq", "wkts_left", "log_balls_left", "crr", "is_t20i"]
    return X, names


def fit_wp(bb, piv):
    ok = clean_match_universe(bb)
    use = bb[bb.match_id.map(ok).fillna(False)].copy()

    # innings 2 ---------------------------------------------------------------
    d2 = use[(use.innings == 2) & (use.runs_needed > 0) & (use.balls_left > 0)].copy()
    d2["y"] = (d2.win_team_id == d2.batting_team_id).astype(int)
    X2, n2 = chase_features(d2, piv)
    m2 = Logit(l2=5.0).fit(X2, d2.y.to_numpy(), names=n2)

    # innings 1 ---------------------------------------------------------------
    d1 = use[use.innings == 1].copy()
    d1["y"] = (d1.win_team_id == d1.batting_team_id).astype(int)
    X1, n1 = inn1_features(d1, piv)
    m1 = Logit(l2=5.0).fit(X1, d1.y.to_numpy(), names=n1)

    diag = {
        "n_matches_fit": int(ok.sum()),
        "n_matches_excluded": int((~ok).sum()),
        "inn2": {"n": len(d2), "log_loss": log_loss(d2.y, m2.predict(X2)),
                 "brier": brier(d2.y, m2.predict(X2)),
                 "base_rate": float(d2.y.mean()),
                 "coefs": m2.coef_table().to_dict("records"),
                 "calibration": calibration(d2.y, m2.predict(X2)).to_dict("records")},
        "inn1": {"n": len(d1), "log_loss": log_loss(d1.y, m1.predict(X1)),
                 "brier": brier(d1.y, m1.predict(X1)),
                 "base_rate": float(d1.y.mean()),
                 "coefs": m1.coef_table().to_dict("records"),
                 "calibration": calibration(d1.y, m1.predict(X1)).to_dict("records")},
    }
    return m1, m2, diag, ok


def wp_batting(d, piv, m1, m2):
    """Win probability for the team currently batting, for any pre-ball state."""
    out = np.full(len(d), np.nan)
    i2 = (d.innings == 2).to_numpy()
    if i2.any():
        X, _ = chase_features(d[i2], piv)
        p = m2.predict(X)
        sub = d[i2]
        p = np.where(sub.runs_needed.to_numpy() <= 0, 1.0, p)
        p = np.where((sub.balls_left.to_numpy() <= 0) | (sub.wkts_left.to_numpy() <= 0),
                     np.where(sub.runs_needed.to_numpy() <= 0, 1.0, 0.0), p)
        out[i2] = p
    i1 = ~i2
    if i1.any():
        X, _ = inn1_features(d[i1], piv)
        out[i1] = m1.predict(X)
    return np.clip(out, 0.0, 1.0)


# --------------------------------------------------------------------------- #
# 4. outcome distribution + leverage
# --------------------------------------------------------------------------- #
def tag_outcomes(bb):
    d = bb.copy()
    illegal = d.extras_type.isin({"wide", "Overstep"})
    runs = d.total_runs.to_numpy()
    base = np.where(runs >= 5, np.where(d.is_six.to_numpy(), 6, 4), runs)
    lab = np.where(illegal, "ox", np.where(d.is_wicket.to_numpy(), "ow",
                                           pd.Series(base).map(
                                               {0: "o0", 1: "o1", 2: "o2", 3: "o3",
                                                4: "o4", 6: "o6"}).fillna("o1").to_numpy()))
    return lab


def over_bucket(ov):
    return pd.cut(ov, [0, 6, 11, 15, 17, 30],
                  labels=["1-6", "7-11", "12-15", "16-17", "18-20"])


def outcome_distribution(bb):
    d = bb.copy()
    lab = tag_outcomes(d)
    for o in OUTCOMES:
        d[o] = (lab == o).astype(float)
    d["ovb"] = over_bucket(d.phase_over)
    d["wl"] = d.wkts_left.clip(0, 10)
    d["rrrb"] = pd.cut(d.rrr.fillna(-1), [-2, 0, 7, 9, 11, 13, 50],
                       labels=["inn1", "<7", "7-9", "9-11", "11-13", "13+"])
    levels = [["match_format", "innings", "ovb", "wl", "rrrb"],
              ["match_format", "innings", "ovb", "wl"],
              ["innings", "ovb", "wl"],
              ["innings", "ovb"]]
    probs, lvl = hierarchical_mean(d, OUTCOMES, levels, min_n=250)
    probs = probs.div(probs.sum(axis=1), axis=0)
    return probs, lvl


def leverage(bb, probs, piv, m1, m2):
    """Expected absolute win-probability swing from the next delivery."""
    base = wp_batting(bb, piv, m1, m2)
    swing = np.zeros(len(bb))

    for o in OUTCOMES:
        nxt = bb.copy()
        r = OUT_RUNS[o]
        consumes_ball = o != "ox"
        nxt["score_before"] = bb.score_before + r
        nxt["wkts_before"] = bb.wkts_before + (1 if o == "ow" else 0)
        nxt["balls_used"] = bb.balls_used + (1 if consumes_ball else 0)
        nxt["wkts_left"] = (10 - nxt.wkts_before).clip(lower=0)
        nxt["balls_left"] = (nxt.balls_avail - nxt.balls_used).clip(lower=0)
        nxt["runs_needed"] = np.where(nxt.innings == 2, nxt.target - nxt.score_before, np.nan)

        p = wp_batting(nxt, piv, m1, m2)
        # Terminal states override the model.
        over = ((nxt.balls_left <= 0) | (nxt.wkts_left <= 0)).to_numpy()
        i2 = (nxt.innings == 2).to_numpy()
        chased = i2 & (nxt.runs_needed.to_numpy() <= 0)
        p = np.where(chased, 1.0, p)
        p = np.where(i2 & over & ~chased, 0.0, p)
        swing += probs[o].to_numpy() * np.abs(p - base)

    return base, swing
