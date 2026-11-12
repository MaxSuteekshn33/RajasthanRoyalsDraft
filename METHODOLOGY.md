# Identifying the Most Reliable Players Under Pressure

**SupeRR Selector Season 2 — Round 1 Methodology Report**
Rajasthan Royals · IPL 2027 Auction

---

## Executive summary

We scored all **200,961 deliveries** in the supplied data pack (867 matches; IPL 2022–2026 plus T20 Internationals) on a continuous, role-relative **Pressure Index**, then measured every player against what the situation normally yields rather than against a raw average.

Three findings shaped the final model:

1. **Pressure does not slow batters down — it gets them out.** Run rate across pressure bands moves by −4.5%, but the dismissal rate **doubles (+101%)** and runs per dismissal fall **52%** (30.2 → 14.4). Pressure charges a risk premium, not a scoring penalty. Any metric built on strike rate alone cannot see it.
2. **Pressure is role-relative.** A run of dot balls strangles the batter but is pressure the *bowler is applying*. We score every delivery twice, once from each side. Making the "build-up" pillar asymmetric is what finally made the bowling signal behave.
3. **"Clutch" is largely not a repeatable skill.** Split-half reliability of the clutch premium is **r = 0.02** for batters (0.15 for bowlers), while overall impact repeats at **r = 0.46**. We therefore shrink each player's pressure record toward *their own overall standard*, not the league average.

### Final rankings

| # | Batters under pressure | SupeRR | # | Bowlers under pressure | SupeRR |
|---|---|---|---|---|---|
| 1 | **Tim David** | 78.4 | 1 | **Josh Hazlewood** | 67.0 |
| 2 | Namboori Tilak Varma | 65.8 | 2 | Nathan Ellis | 64.6 |
| 3 | Shreyas Iyer | 66.6 | 3 | Jasprit Bumrah | 65.4 |
| 4 | Suryakumar Yadav | 70.0 | 4 | Sunil Narine | 64.1 |
| 5 | Heinrich Klaasen | 65.6 | 5 | Rashid Khan | 63.7 |
| 6 | Jos Buttler | 60.9 | 6 | Matheesha Pathirana | 62.5 |
| 7 | Mitchell Marsh | 56.9 | 7 | Varun Chakravarthy | 61.6 |
| 8 | Rinku Singh | 54.4 | 8 | Jofra Archer | 61.1 |
| 9 | Rovman Powell | 55.1 | 9 | Eshan Malinga | 59.4 |
| 10 | Andre Russell | 54.4 | 10 | Wanindu Hasaranga | 59.0 |

Order is the **consensus across 13 modelling variants**, not a single parameter choice. SupeRR is the baseline-run composite rating (50 = pool average), shown for reference — which is why it is not perfectly monotonic with the consensus order.

---

## 1. Pressure definition

The brief left the definition to us. We made two structural choices up front.

**Pressure is continuous, not a death-overs switch.** Treating overs 16–20 as "pressure" and everything else as "not" discards the hardest ball of a collapsing powerplay and includes a dead rubber's final over. We score every delivery 0–100.

**Pressure is role-relative.** The same delivery is agony for one player and opportunity for the other. We compute `PI_bat` and `PI_bowl` separately.

### The four pillars

```
PI = 0.40·Leverage + 0.25·Adversity + 0.20·Scarcity + 0.15·Build-up
     ×  knockout multiplier (1.08)
```

| Pillar | Weight | What it captures | How it is computed |
|---|---|---|---|
| **Leverage** | 40% | How much this ball can swing the result | Expected \|ΔWin Probability\| from one delivery, obtained by enumerating the eight possible outcomes (0/1/2/3/4/6, wicket, extra) against their state-conditional probabilities |
| **Adversity** | 25% | How badly your own side is placed | `1 − WP(own team)`. This is the pillar that makes pressure role-relative |
| **Scarcity** | 20% | How much batting resource is spent | Read off a fitted Duckworth-Lewis-style resource curve, so balls and wickets are priced on one scale |
| **Build-up** | 15% | The squeeze over the previous 12 balls | **Asymmetric**: dots + wickets for the batter; runs + boundaries conceded for the bowler. One-ball lag so a delivery is never scored using its own outcome |

Leverage carries the most weight because it is the one pillar derived from a fitted statistical model. The other three capture cricketing texture a win-probability model alone misses.

A ball scoring **PI ≥ 65** is classified as a pressure ball (12.9% of deliveries for batting, 12.1% for bowling). This threshold is used for *reporting only* — the ratings themselves use continuous weighting.

### Supporting models

| Model | Purpose | Performance |
|---|---|---|
| Chase win probability | Leverage + adversity, 2nd innings | **Brier 0.128**, log loss 0.392 (coin flip = 0.25). Calibration near-perfect across all ten deciles |
| 1st-innings win probability | Same, 1st innings | Brier 0.221 — materially weaker (see Limitations) |
| Resource curve `R(balls, wickets)` | Scarcity + wicket cost | DL-form `Z(1−e^{−λb/Z})` fitted per wicket column, blended with empirical cell means. Reproduces the actual mean first-innings total to within 0.5 runs (176.5 vs 176.0) |

All models are hand-rolled on numpy/pandas — the logistic regression is IRLS, the DL fit is a refined grid search. No library defaults are hidden anywhere in the pipeline.

---

## 2. Performance measurement

Strike rate and economy are the wrong currency: what a good ball is worth depends entirely on the situation. We price everything in **runs above expectation**.

```
batter impact = (runs − xRuns) − wicketCost × (out − xWicket)
bowler impact = (xRuns − runs) + wicketCost × (wicket − xWicket)
```

- **`xRuns` / `xWicket`** — what the average player manages in that exact situation. Estimated by hierarchical empirical means over `(context, phase, wickets in hand, pressure band, pace/spin)`, falling back to coarser keys when a cell holds fewer than 200 deliveries.
  Critically, **the pressure band is part of the conditioning**. Pressure balls are judged against pressure norms, which is what stops the death overs flattering everyone who bats there.
- **`wicketCost`** — the batting resource a dismissal destroys, read off the resource curve: ~16 runs in the powerplay down to 2–4 at the death. Fully data-derived, not assumed.
- Run-outs are excluded from bowler credit; byes and leg-byes from bowler debit; non-striker dismissals from the striker's record.

### Rating construction

**Weight, don't filter.** A hard PI ≥ 65 cut-off left only 66 batters with 100+ pressure balls — too thin to rank on. Instead every delivery contributes with weight `u^1.5` where `u = (PI − 45)/55`, so the estimate uses all 201k balls while still being dominated by the hard ones. Recency is applied on top (`0.78^seasons-ago`), because this is an auction decision.

**Shrink toward the player, not the league.** Because overall form repeats (r = 0.46) and clutch does not (r = 0.02), the statistically correct prior for a player's pressure performance is *their own overall record*:

```
overall_hat = shrink(overall impact, league mean,  k = 782)
press_hat   = shrink(pressure impact, overall_hat, k = 245)
```

Ballasts `k` are derived from measured split-half reliability (`k = n̄(1−r)/r`), not chosen by taste. This is also what a good selector does by instinct: assume a quality player will cope until their pressure record says otherwise, loudly and repeatedly.

**Let components earn their weight.** Each component's base weight is scaled by the square root of its measured reliability and renormalised:

| Component | Batting weight | Bowling weight |
|---|---|---|
| Pressure estimate | 88.3% | 63.1% |
| Match consistency | 6.7% | 23.6% |
| Clutch premium | 5.0% | 13.3% |

The weights differ by role *because the reliability differs by role* — bowling consistency repeats (r = 0.24), batting consistency does not (r ≈ 0.01).

---

## 3. Fair comparisons

| Issue | Treatment |
|---|---|
| **Opposition quality** | Teams graded on their own league-wide record in the data (runs conceded per ball for attacks, runs scored for batting units), split into terciles weighted by volume. A batter's context is the attack he faced; a bowler's is the batting unit he bowled at. Runs against a weak attack carry a higher `xRuns` and are therefore discounted automatically |
| **IPL vs T20I** | Competition type is a dimension of the expectation model (`ipl` / `t20i` / `dev`). Emerging-Teams and Rising-Stars competitions are separated out |
| **Sample size** | Two-level empirical-Bayes shrinkage with data-derived ballasts; effective sample size reported per player |
| **Eligibility** | ≥90 pressure deliveries, ≥400 total deliveries, ≥12 matches. Batters additionally require a median batting position ≤7 — a No. 8 who hits well is a useful asset but not a top-10 *batter* |
| **Recency** | Exponential season decay (0.78), so 2026 form outweighs 2022 |
| **Phase confounding** | Validated within-phase (below), not just across the whole dataset |

**Final pools: 47 eligible batters, 66 eligible bowlers.**

---

## 4. Evidence

### Test 1 — Output degrades as PI rises

| PI band | Balls | Run rate | Wkts/100 | **Runs per dismissal** |
|---|---|---|---|---|
| 0–20 | 7,742 | 9.80 | 5.41 | **30.2** |
| 20–35 | 22,154 | 9.83 | 5.22 | **31.4** |
| 35–50 | 64,553 | 9.00 | 5.09 | **29.5** |
| 50–65 | 73,317 | 8.36 | 5.52 | **25.2** |
| 65–80 | 20,833 | 8.75 | 7.41 | **19.7** |
| 80–100 | 3,813 | 9.36 | 10.86 | **14.4** |

Run rate is essentially flat; survival collapses. This is the central empirical result.

### Test 2 — The signal survives controlling for phase

Top vs bottom PI tercile *within* each phase:

| Phase | Batting: runs/dismissal gap | Bowling: economy gap |
|---|---|---|
| Overs 1–6 | −10.0% | +0.18 rpo |
| Overs 7–11 | −16.7% | +0.69 rpo |
| Overs 12–15 | −27.5% | +1.32 rpo |
| Overs 16–17 | −35.8% | +1.59 rpo |
| Overs 18–20 | −34.6% | +1.76 rpo |

The index is not merely a proxy for "which over is it".

### Test 3 — No single pillar carries the result

Runs-per-dismissal gap by index variant:

| Phase | Full index | Without build-up | Leverage only |
|---|---|---|---|
| 1–6 | −10.0% | −5.0% | −2.1% |
| 7–11 | −16.7% | −13.5% | +2.0% |
| 12–15 | −27.5% | −18.6% | +1.4% |
| 16–17 | −35.8% | −18.6% | −0.2% |
| 18–20 | −34.6% | −24.7% | −21.7% |

Build-up is the pillar most at risk of flattering the result (recent scoring autocorrelates with the current ball). Removing it shrinks the gap by roughly a third but does not remove it. **Leverage alone separates almost nothing outside the death overs** — which is precisely why the index is a composite and not just a win-probability model.

### Test 4 — Stability of the shortlist

Thirteen variants: pressure floor 35/45/55, linear/convex/steep weighting, recency 0.60/0.78/1.00, three component-weighting schemes, three alternative pillar balances, and a stricter eligibility bar.

- **Rank correlations: 0.70 – 0.99**
- **Mean top-10 retained: 7.2/10 batters, 7.5/10 bowlers**
- Tim David ranks 1st or 2nd in **all 13**; Bumrah, Rashid, Varun Chakravarthy, Pathirana and Archer are top-10 eligible in all 13

The published order is the consensus (mean percentile position across variants), with each player's rank standard deviation shown alongside.

### Why these ten

| Player | The case |
|---|---|
| **Tim David** | Strike rate *rises* under pressure (187 vs 173) while he survives longer than peers in the same spots. 309 pressure balls. Rank 1–2 in every variant |
| **Tilak Varma** | Most pressure deliveries faced in the pool (440) and still well above expectation. Clutch delta +0.24 |
| **Shreyas Iyer** | Largest pressure-minus-calm gap among top-ranked batters (+0.24); proven at rebuilding a collapse |
| **Suryakumar Yadav** | Elite in both regimes rather than a specialist; second-largest sample. Highest floor on the board |
| **Josh Hazlewood** | Best raw pressure impact of any bowler (+0.36/ball) with a positive clutch delta |
| **Nathan Ellis** | Death specialist whose value is concentrated exactly where PI is highest |
| **Jasprit Bumrah** | Best overall bowling impact in the dataset; barely moves under pressure because he is simply this good all the time |

---

## 5. Reliability and limitations

**Split-half reliability** (matches dealt alternately by date; Spearman-Brown corrected to full length):

| Metric | Batting | Bowling | Verdict |
|---|---|---|---|
| Overall impact/ball | 0.46 | 0.30 | Real, durable skill |
| Pressure impact/ball | 0.17 | 0.16 | Weak but real |
| Clutch premium | 0.02 | 0.13 | **Noise** |
| Match consistency | 0.01 | 0.24 | Noise (bat) / weak (bowl) |

### Known limitations

1. **This is not a temperament ranking.** It says these ten have the highest *expected output* when PI is high. Reading it as "strongest nerve" over-reads the evidence.
2. **Pressure samples are small** even across five seasons. Error bars on any individual estimate are wide — hence the consensus approach and published rank swings.
3. **No scouting data**: injuries, fitness, contract status, auction availability, age. Nor pitch and dew, which matter most in exactly the death-over situations the model weights heaviest.
4. **First-innings pressure is weaker.** The chase model is strong (Brier 0.128); the first-innings model much weaker (0.221), because without a target the state is less informative. Batters who do their best work *setting* totals are likely under-credited.
5. **Build-up partly measures conditions, not the player** — a slow pitch produces both recent dots and a current dot. Quantified in Test 3 rather than buried.
6. **Residual context bias** for players whose record sits almost entirely in one competition.

### Data integrity

- **806 of 838** matches reproduce the official result margin exactly from our rebuilt innings totals. The remainder are D/L-adjusted or abandoned, plus one wicket-count discrepancy.
- **A real bug, caught and fixed:** extras tagged `other` were being counted as legal deliveries, pushing 150 innings past 120 balls and corrupting every downstream state. We re-anchored the ball count to the official over number, eliminating all impossible states.
- **The supplied file is truncated** at exactly 201,000 rows, mid-innings. 16 matches in `matches.csv` have no deliveries; the final match is incomplete. All are excluded from model fitting.

---

## 6. Reproducing this

Six ordered Python stages, numpy + pandas only:

| Stage | Purpose |
|---|---|
| `s1_states.py` | Rebuild the live match state behind every ball; validate against result strings |
| `s2_models.py` | Resource curve, win probability, leverage |
| `s3_pressure.py` | Pressure Index + validation |
| `s4_ratings.py` | Expected runs, impact, shrinkage, ratings |
| `s5_sensitivity.py` | 13-variant sweep and consensus ranking |
| `s6_export.py` | Dashboard data bundle |

```bash
cd analysis && python3 s1_states.py && python3 s2_run.py && \
  python3 s3_pressure.py && python3 s4_ratings.py && \
  python3 s5_sensitivity.py && python3 s6_export.py
cd ../dashboard && npm install && npm run dev
```
