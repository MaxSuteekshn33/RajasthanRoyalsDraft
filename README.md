# SupeRR Selector S2 — Pressure Intelligence

Round 1 submission for the Rajasthan Royals *SupeRR Selector Season 2* challenge:
identify the most reliable players under pressure for the IPL 2027 auction.

- **[METHODOLOGY.md](./METHODOLOGY.md)** — the full methodology report
- **`analysis/`** — six-stage Python pipeline (numpy + pandas only)
- **`dashboard/`** — interactive Next.js dashboard

## The answer

**Batters under pressure**

1. Tim David · 2. Namboori Tilak Varma · 3. Shreyas Iyer · 4. Suryakumar Yadav · 5. Heinrich Klaasen
6. Jos Buttler · 7. Mitchell Marsh · 8. Rinku Singh · 9. Rovman Powell · 10. Andre Russell

**Bowlers under pressure**

1. Josh Hazlewood · 2. Nathan Ellis · 3. Jasprit Bumrah · 4. Sunil Narine · 5. Rashid Khan
6. Matheesha Pathirana · 7. Varun Chakravarthy · 8. Jofra Archer · 9. Eshan Malinga · 10. Wanindu Hasaranga

Order is the consensus across 13 modelling variants.

## The headline

Pressure doesn't slow batters down — it gets them out. Across pressure bands run rate moves
−4.5%, while the dismissal rate **doubles** and runs per dismissal fall **52%**.

And "clutch" barely repeats: split-half reliability is **0.02** for batters, against **0.46**
for overall impact. So the model shrinks a player's pressure record toward *their own* standard
rather than the league's — and the component weights are set by measured reliability rather than
by taste.

## Running it

```bash
# pipeline — expects the data pack at ~/Downloads/Data Pack
cd analysis
python3 s1_states.py      # rebuild per-ball match state, validate vs result strings
python3 s2_run.py         # resource curve, win probability, leverage
python3 s3_pressure.py    # Pressure Index + validation
python3 s4_ratings.py     # expected runs, impact, shrinkage, ratings
python3 s5_sensitivity.py # 13-variant sweep, consensus ranking
python3 s6_export.py      # write dashboard data

# dashboard
cd ../dashboard
npm install
npm run dev               # http://localhost:4310
```

## Dashboard

| Tab | What's in it |
|---|---|
| Overview | The headline findings and both top-10 lists |
| Methodology | The four pillars, plus a live pressure calculator over 5,180 precomputed chase states |
| Validation | Three tests that the index measures pressure, and the reliability table that reshaped the model |
| Rankings | Consensus top 10s, a scenario explorer showing how the list moves, and the full sortable pool |
| Player Lab | Per-player pressure vs calm splits, phase and season trends, signature performances |
| RR Squad Fit | The 2026 Royals squad rated, the gaps, and target-by-target rationale |
| Limitations | Where the model is least certain, and the data-integrity checks |
