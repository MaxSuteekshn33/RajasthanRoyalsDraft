"""Shared paths, constants and loaders for the SupeRR Selector pipeline."""
from pathlib import Path

import numpy as np
import pandas as pd

DATA = Path("/Users/suteekshnmahajan/Downloads/Data Pack")
OUT = Path(__file__).parent / "out"
OUT.mkdir(exist_ok=True)

# Deliveries that do not count towards the six legal balls of an over.
# "other" is included on the evidence of the over structure itself: overs
# containing one are seven deliveries long and otherwise tally to seven legal
# balls, so these are unlabelled no-balls.
ILLEGAL_EXTRAS = {"wide", "Overstep", "other"}

# Competitions played by developmental sides rather than senior teams.
DEV_COMP_PATTERNS = ("Emerging", "Rising Stars")

# Senior nations that field full-strength sides; everything else is treated as
# a weaker attack/batting unit when we adjust for opposition quality.
TIER1 = {
    "India", "Australia", "England", "South Africa", "New Zealand",
    "Pakistan", "Sri Lanka", "West Indies", "Bangladesh", "Afghanistan",
}


def load_raw():
    bb = pd.read_csv(DATA / "ball_by_ball.csv", low_memory=False)
    matches = pd.read_csv(DATA / "matches.csv", low_memory=False)
    comps = pd.read_csv(DATA / "competitions.csv")
    teams = pd.read_csv(DATA / "teams.csv")
    mapping = pd.read_csv(DATA / "competition_team_player_mapping.csv")
    return bb, matches, comps, teams, mapping


def zscore(s: pd.Series) -> pd.Series:
    sd = s.std(ddof=0)
    return (s - s.mean()) / sd if sd > 0 else pd.Series(0.0, index=s.index)


def shrink(value: pd.Series, n: pd.Series, prior: float, k: float) -> pd.Series:
    """Empirical-Bayes style shrinkage of a per-ball rate toward a prior.

    k is the 'ballast': the number of balls at which a player's own record and
    the prior carry equal weight.
    """
    w = n / (n + k)
    return w * value + (1 - w) * prior
