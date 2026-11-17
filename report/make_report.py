"""Assemble the SupeRR Selector report as print-ready HTML, then PDF via Chrome."""
import base64
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FIG = ROOT / "figures"
DATA = ROOT.parent / "dashboard" / "src" / "data"

meta = json.load(open(DATA / "meta.json"))
diag = json.load(open(DATA / "diagnostics.json"))
press = diag["pressure"]
relb = diag["ratings"]["reliability_batting"]["metrics"]
rell = diag["ratings"]["reliability_bowling"]["metrics"]
squad = json.load(open(DATA / "squad.json"))
pbat = json.load(open(DATA / "players_bat.json"))
pbowl = json.load(open(DATA / "players_bowl.json"))


def top10(ps):
    return sorted([p for p in ps if p.get("consensus_rank")],
                  key=lambda p: p["consensus_rank"])[:10]


BAT, BOWL = top10(pbat), top10(pbowl)


def img(name):
    b = base64.b64encode((FIG / name).read_bytes()).decode()
    return f"data:image/png;base64,{b}"


# --------------------------------------------------------------------------
# the written case for each selection, grounded in the numbers above it
# --------------------------------------------------------------------------
CASE_BAT = {
 "Tim David": ("The outstanding pressure asset in the dataset, and the only player to finish "
   "1st or 2nd in all thirteen modelling variants (rank SD 0.48 — nothing else is close). "
   "His strike rate <em>rises</em> under pressure, 187 against 173, which is rare enough on "
   "its own. The decisive number is survival: his balls-per-dismissal falls 22% (21.0 → 16.3) "
   "against a league norm that roughly halves. He is absorbing the risk premium pressure "
   "charges everyone else.", "Buy — the model's clearest single recommendation"),
 "Namboori Tilak Varma": ("Faced more pressure deliveries than any other batter in the pool "
   "(440) and still finished well above expectation, with the second-largest clutch premium "
   "in the top ten (+0.24). His dismissal rate is <em>flat</em> across regimes — 29.0 balls "
   "per dismissal calm, 29.3 under pressure — while the field's halves. Young, Indian, "
   "left-handed, and equally able to rebuild or finish.", "Buy — highest ceiling, Indian core"),
 "Shreyas Iyer": ("The largest pressure-minus-calm gap of any top-ranked batter (+0.235). "
   "Strike rate jumps from 151 to 181 while he still survives longer than the norm "
   "(21.9 balls per dismissal). Captaincy experience and a proven record of batting through a "
   "collapse — precisely the failure mode the current Royals middle order exhibits. Sample is "
   "moderate at 175 pressure balls.", "Buy — fills the rebuild-and-accelerate gap"),
 "Suryakumar Yadav": ("Elite in both regimes rather than a pressure specialist: +0.32 under "
   "pressure against +0.28 calm, on the second-largest sample in the pool (340 pressure balls, "
   "139 matches). His strike rate actually eases slightly (167 → 159) but his dismissal rate "
   "rises far less than the field's. The highest-floor name on the board — if the brief were "
   "'who will not let you down', this is the pick.", "Buy — the safety-first option"),
 "Heinrich Klaasen": ("The highest pressure strike rate in the top ten at 189, with a clutch "
   "premium of +0.11 and 85% of his evidence coming from the IPL itself. Balls per dismissal "
   "falls from 25.1 to 16.8 — he does take on more risk — but the runs more than pay for it. "
   "Keeps wicket, which would let the Royals carry an extra bowler.",
   "Buy — if an overseas slot is free"),
 "Jos Buttler": ("Returns a positive pressure contribution in 93% of his matches, the highest "
   "consistency figure in the entire batting pool. Strike rate climbs 154 → 183 when the "
   "situation tightens. The caveat is sample: 116 pressure deliveries is the thinnest evidence "
   "base in this top ten, which is why he sits 6th rather than higher. Knows the franchise.",
   "Buy — consistency, with a sample-size asterisk"),
 "Mitchell Marsh": ("Makes the ten on the strength of his overall standard rather than any "
   "pressure premium — his clutch delta is −0.002, and his strike rate actually falls under "
   "pressure (158 → 146). The model ranks him 7th because the hierarchical estimator trusts a "
   "strong, well-sampled baseline. Read him as a quality batter who neither lifts nor folds, "
   "not as a finisher.", "Hold — quality, but no pressure premium"),
 "Rinku Singh": ("A genuine clutch profile on a solid sample: +0.134 premium across 208 "
   "pressure deliveries, 68% of it in the IPL. Strike rate holds (152 → 154) while balls per "
   "dismissal improves relative to the field. Bats at six, Indian, and already proven in the "
   "exact slot the Royals need to fill.", "Buy — domestic finisher, strong value"),
 "Rovman Powell": ("One of the larger clutch premiums in the pool (+0.17) across 285 pressure "
   "deliveries. The caveat is context: only 25% of his record comes from the IPL, so the "
   "majority of the evidence is West Indies T20I cricket. The opposition-strength adjustment "
   "discounts this, but a buyer should weight the IPL sample heavily before committing.",
   "Watch — evidence is mostly non-IPL"),
 "Andre Russell": ("Included for completeness and flagged, not recommended. He makes the "
   "consensus ten on an excellent overall record (+0.27 per ball), but his pressure record is "
   "materially <em>below</em> his own standard — a clutch delta of −0.168, the worst in either "
   "top ten. He is also the least stable name in the sweep (rank SD 6.8, eligible in only 10 of "
   "13 variants) and was last seen in the 2025 data. The model's own logic argues against "
   "paying a premium here.", "Avoid — negative clutch, declining recency"),
}

CASE_BOWL = {
 "Josh Hazlewood": ("The best raw pressure impact of any bowler in the dataset (+0.356 per "
   "ball). Under pressure he takes a wicket every 8.3 deliveries against 17.4 when calm — the "
   "strike rate more than doubles. Economy does rise (7.95 → 8.95), but by far less than the "
   "phase norm. Relentlessly repeatable, and the natural partner at the other end to Archer.",
   "Buy — top-rated bowler on the consensus"),
 "Nathan Ellis": ("A death specialist whose value sits exactly where the Pressure Index peaks: "
   "211 pressure deliveries from only 43 matches. Economy is essentially unchanged between "
   "regimes (7.85 calm, 7.99 under pressure) while his wicket rate improves sharply (18.7 → "
   "11.7 balls per wicket). Only 34% of the record is IPL, and he is unlikely to command a "
   "marquee price.", "Buy — best value in the bowling ten"),
 "Jasprit Bumrah": ("The best overall bowling impact in the dataset (+0.214) with a clutch "
   "delta of +0.007 — he neither lifts nor dips, because he is simply this good all the time. "
   "Economy rises from 6.75 to 8.36 under pressure, which still beats the norm comfortably. "
   "Top-ten eligible in all thirteen variants. The most expensive route to this outcome.",
   "Buy — if budget allows; no premium for clutch"),
 "Sunil Narine": ("One of only two bowlers in the ten whose economy <em>improves</em> under "
   "pressure (6.81 → 6.51). Entirely IPL-proven — 100% of his record is franchise cricket — "
   "and he carries genuine top-order batting value, effectively two squad slots for one. "
   "Spin that holds up in the powerplay and the middle alike.",
   "Buy — two roles, one slot"),
 "Rashid Khan": ("The benchmark middle-overs wicket-taker: economy improves under pressure "
   "(7.37 → 7.14), balls per wicket falls from 19.3 to 12.2, across the largest spin sample in "
   "the pool (305 pressure deliveries, 122 matches) and top-ten eligible in all thirteen "
   "variants. Consistency of 0.68 is strong for a wrist-spinner.",
   "Buy — the most proven name available"),
 "Matheesha Pathirana": ("Ranks sixth on the strength of an excellent overall record (+0.197) "
   "rather than a pressure premium — his clutch delta is −0.046 and his economy rises from "
   "7.63 to 8.64. The slingy action remains hardest to line up precisely when batters must "
   "take risks, and at 261 pressure deliveries the sample is solid. Young enough to be a "
   "multi-season asset.", "Buy — long-horizon asset, modest premium"),
 "Varun Chakravarthy": ("Mystery spin that keeps taking wickets as pressure rises rather than "
   "retreating into a defensive line — balls per wicket improves from 16.4 to 14.6, with a "
   "small positive clutch delta (+0.046). Top-ten eligible in all thirteen variants on a large "
   "sample. Match consistency of 0.52 is the one soft spot.",
   "Buy — covers the middle-overs strike gap"),
 "Jofra Archer": ("<strong>Already contracted to Rajasthan.</strong> His wicket rate nearly "
   "doubles under pressure — 20.2 balls per wicket when calm against 11.4 when it matters — "
   "with economy effectively flat (8.64 → 8.68) and a clutch premium of +0.125. The caveat is "
   "volatility: rank SD of 7.1 is the highest in either list, so his precise position is "
   "uncertain even though his top-ten status is not.",
   "Retain — the squad's one elite pressure asset"),
 "Eshan Malinga": ("The value pick of the bowling list. Economy improves under pressure "
   "(8.51 → 7.98) and his clutch premium of +0.146 is among the strongest here. The honest "
   "caveat is evidence: 118 pressure deliveries is the smallest sample in this ten, he is "
   "eligible in only 10 of 13 variants, and his rank swings by ±5. Cheap enough that the risk "
   "is affordable.", "Buy — low cost, genuine upside"),
 "Wanindu Hasaranga": ("A strong clutch premium (+0.119) and a wicket rate that improves from "
   "16.1 to 12.0 balls per wicket under pressure, across 265 pressure deliveries. The "
   "reservation is reliability: match consistency of 0.47 is the lowest in either top ten, "
   "meaning the good games are very good and the bad ones are costly. A boom-or-bust option "
   "rather than a floor-raiser.", "Watch — high ceiling, low floor"),
}


def pill(text, tone="rr"):
    return f'<span class="pill {tone}">{text}</span>'


def verdict_tone(v):
    head = v.split("—")[0].strip().lower()
    return {"buy": "good", "retain": "good", "hold": "warn",
            "watch": "warn", "avoid": "bad"}.get(head, "muted")


def bat_rows():
    out = []
    for p in BAT:
        out.append(f"""<tr>
  <td class="rk">{p['consensus_rank']}</td>
  <td class="nm">{p['name']}</td>
  <td>{p['superrr']:.1f}</td>
  <td>{p['impact_press']:+.3f}</td>
  <td>{p['clutch']:+.3f}</td>
  <td>{p['pressure']['strike_rate']:.0f}</td>
  <td>{p['press_balls']}</td>
  <td>{p['matches']}</td>
  <td>&plusmn;{p['rank_sd']:.1f}</td>
</tr>""")
    return "\n".join(out)


def bowl_rows():
    out = []
    for p in BOWL:
        out.append(f"""<tr>
  <td class="rk">{p['consensus_rank']}</td>
  <td class="nm">{p['name']}</td>
  <td>{p['superrr']:.1f}</td>
  <td>{p['impact_press']:+.3f}</td>
  <td>{p['clutch']:+.3f}</td>
  <td>{p['pressure']['economy']:.2f}</td>
  <td>{p['press_balls']}</td>
  <td>{p['matches']}</td>
  <td>&plusmn;{p['rank_sd']:.1f}</td>
</tr>""")
    return "\n".join(out)


def dossier(p, role):
    cases = CASE_BAT if role == "bat" else CASE_BOWL
    case, verdict = cases.get(p["name"], ("", ""))
    pr, ca = p["pressure"], p["calm"]
    if role == "bat":
        stats = [("Pressure SR", f"{pr['strike_rate']:.0f}", f"calm {ca['strike_rate']:.0f}"),
                 ("Balls / dismissal", f"{pr['balls_per_dismissal']:.1f}",
                  f"calm {ca['balls_per_dismissal']:.1f}"),
                 ("Pressure runs", f"{pr['runs']:.0f}", f"{pr['balls']} balls")]
    else:
        stats = [("Pressure economy", f"{pr['economy']:.2f}", f"calm {ca['economy']:.2f}"),
                 ("Balls / wicket", f"{pr['balls_per_wicket']:.1f}",
                  f"calm {ca['balls_per_wicket']:.1f}"),
                 ("Pressure wickets", f"{pr['wickets']:.0f}", f"{pr['balls']} balls")]
    stats += [("Clutch premium", f"{p['clutch']:+.3f}", "pressure minus calm"),
              ("Pressure impact", f"{p['impact_press']:+.3f}", "runs added per ball"),
              ("Stability", f"&plusmn;{p['rank_sd']:.1f}", f"{p['scenarios_eligible']}/13 variants")]
    cells = "".join(
        f'<div class="st"><div class="sl">{l}</div><div class="sv">{v}</div>'
        f'<div class="ss">{s}</div></div>' for l, v, s in stats)
    teams = " · ".join(p["teams"][:3])
    ipl = f"{p['ipl_share']*100:.0f}% IPL"
    return f"""<div class="dossier">
  <div class="dhead">
    <div class="dbadge">{p['consensus_rank']}</div>
    <div class="dname">
      <h4>{p['name']}</h4>
      <div class="dmeta">{teams} &nbsp;·&nbsp; {ipl} &nbsp;·&nbsp; {p['matches']} matches &nbsp;·&nbsp; last seen {p['last_season']}</div>
    </div>
    <div class="dverdict {verdict_tone(verdict)}">{verdict}</div>
  </div>
  <div class="dstats">{cells}</div>
  <p class="dcase">{case}</p>
</div>"""


def squad_rows():
    rated = [p for p in squad["squad"] if p["bat_rank"] or p["bowl_rank"]]
    out = []
    for p in rated:
        br = f"#{p['bat_rank']}/{p['bat_pool']}" if p["bat_rank"] else "—"
        lr = f"#{p['bowl_rank']}/{p['bowl_pool']}" if p["bowl_rank"] else "—"
        bs = f"{p['bat_superrr']:.1f}" if p["bat_superrr"] else "—"
        ls = f"{p['bowl_superrr']:.1f}" if p["bowl_superrr"] else "—"
        good = (p["bat_rank"] or 99) <= 15 or (p["bowl_rank"] or 99) <= 15
        out.append(f'<tr class="{"hl" if good else ""}"><td class="nm">{p["name"]}</td>'
                   f"<td>{br}</td><td>{bs}</td><td>{lr}</td><td>{ls}</td></tr>")
    return "\n".join(out)


BANDS = "".join(
    f"<tr><td class='nm'>{r['band']}</td><td>{r['balls']:,}</td><td>{r['run_rate']:.2f}</td>"
    f"<td>{r['wkt_per_100']:.2f}</td><td class='em'>{r['runs_per_dismissal']:.1f}</td></tr>"
    for r in press["batting_by_pi"])

REL_ROWS = "".join(
    f"<tr><td class='nm'>{lab}</td><td>{relb[k]['full_length_r']:.2f}</td>"
    f"<td>{rell[k]['full_length_r']:.2f}</td><td class='{tone}'>{verd}</td></tr>"
    for lab, k, verd, tone in [
        ("Overall impact / ball", "overall", "Real, durable skill", "good"),
        ("Pressure impact / ball", "press", "Weak but real", "warn"),
        ("Clutch premium", "clutch", "Noise", "bad"),
        ("Match consistency", "pos_rate", "Noise (bat) / weak (bowl)", "bad")])

HTML = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>SupeRR Selector — Round 1 Report</title>
<style>
@page {{ size: A4; margin: 15mm 14mm 16mm 14mm; }}
@page coverpage {{ size: A4; margin: 0; }}

* {{ box-sizing: border-box; }}
html {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
body {{ font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; color: #14142b;
  font-size: 9.6pt; line-height: 1.55; margin: 0; }}
h1,h2,h3,h4 {{ margin: 0; line-height: 1.2; }}
p {{ margin: 0 0 8pt; }}
em {{ font-style: italic; }}
.page-break {{ page-break-before: always; }}
.avoid {{ page-break-inside: avoid; }}

/* cover */
.cover {{ page: coverpage; height: 100vh; width: 100%; position: relative;
  overflow: hidden;
  background: linear-gradient(150deg,#0a0b2e 0%,#1a1040 42%,#5e0f44 78%,#8d1157 100%);
  color: #fff; padding: 28mm 20mm; display: flex; flex-direction: column; }}
.cover::after {{ content:""; position:absolute; right:-70mm; top:-50mm; width:190mm;
  height:190mm; border-radius:50%; background: radial-gradient(circle,
  rgba(230,23,127,.42),rgba(230,23,127,0) 68%); }}
.cmark {{ display:flex; align-items:center; gap:9pt; position:relative; z-index:2; }}
.clogo {{ width:34pt; height:34pt; border-radius:9pt; background:#e6177f; display:grid;
  place-items:center; font-weight:800; font-size:14pt; letter-spacing:.5pt; }}
.ctitle {{ font-size:33pt; font-weight:800; letter-spacing:-.6pt; margin-top:auto;
  position:relative; z-index:2; }}
.ctitle span {{ color:#ff86bd; }}
.csub {{ font-size:12pt; color:#cfd0ee; margin-top:9pt; max-width:140mm;
  position:relative; z-index:2; line-height:1.5; }}
.cstats {{ display:flex; gap:7mm; margin-top:14mm; position:relative; z-index:2;
  border-top:1px solid rgba(255,255,255,.22); padding-top:7mm; }}
.cstat b {{ display:block; font-size:19pt; font-weight:800; }}
.cstat span {{ font-size:8pt; color:#b9bae0; text-transform:uppercase;
  letter-spacing:.9pt; }}
.cfoot {{ margin-top:12mm; font-size:8.6pt; color:#a9aad6; position:relative; z-index:2; }}

/* structure */
.kicker {{ font-size:7.6pt; font-weight:800; letter-spacing:1.6pt; text-transform:uppercase;
  color:#d11a76; margin-bottom:3pt; }}
h2 {{ font-size:17pt; font-weight:800; letter-spacing:-.3pt; margin-bottom:5pt; }}
h3 {{ font-size:11.4pt; font-weight:800; margin:13pt 0 5pt; }}
h4 {{ font-size:10.6pt; font-weight:800; }}
.lede {{ font-size:10.4pt; color:#43435f; margin-bottom:10pt; }}
.rule {{ height:2.5pt; width:34pt; background:#e6177f; border-radius:2pt; margin:7pt 0 11pt; }}
.muted {{ color:#6b6b86; }}
.small {{ font-size:8.4pt; }}

/* tables */
table {{ width:100%; border-collapse:collapse; margin:7pt 0 10pt; font-size:8.8pt; }}
th {{ text-align:right; font-size:7.4pt; text-transform:uppercase; letter-spacing:.7pt;
  color:#6b6b86; border-bottom:1.2pt solid #14142b; padding:4pt 4pt; font-weight:700; }}
th:first-child, th.l {{ text-align:left; }}
td {{ text-align:right; padding:4pt 4pt; border-bottom:.6pt solid #e4e4ed;
  font-variant-numeric:tabular-nums; }}
td.nm {{ text-align:left; font-weight:600; }}
td.rk {{ text-align:left; font-weight:800; color:#d11a76; width:20pt; }}
td.em {{ font-weight:800; }}
tr.hl td {{ background:#fdeaf4; }}
td.good {{ color:#0a7c53; font-weight:700; }}
td.warn {{ color:#9a6700; font-weight:700; }}
td.bad {{ color:#c01c4a; font-weight:700; }}

/* pills + boxes */
.pill {{ display:inline-block; padding:1.5pt 6pt; border-radius:20pt; font-size:7.6pt;
  font-weight:700; }}
.pill.rr {{ background:#fdeaf4; color:#b3135f; }}
.pill.gold {{ background:#fdf3dc; color:#8a6400; }}
.pill.sky {{ background:#e7f1fc; color:#1d5fa8; }}
.box {{ border:1pt solid #e4e4ed; border-left:3pt solid #e6177f; border-radius:6pt;
  padding:9pt 11pt; margin:9pt 0; background:#fcfcfe; }}
.box h4 {{ margin-bottom:3pt; }}
.grid3 {{ display:grid; grid-template-columns:repeat(3,1fr); gap:7pt; margin:9pt 0; }}
.grid2 {{ display:grid; grid-template-columns:repeat(2,1fr); gap:9pt; margin:9pt 0; }}
.card {{ border:1pt solid #e4e4ed; border-radius:7pt; padding:9pt 10pt; background:#fff; }}
.card .n {{ font-size:15pt; font-weight:800; color:#d11a76; line-height:1; }}
.card h4 {{ margin:5pt 0 3pt; font-size:9.6pt; }}
.card p {{ font-size:8.5pt; color:#50506c; margin:0; }}
figure {{ margin:10pt 0 12pt; }}
figure img {{ width:100%; display:block; }}
figcaption {{ font-size:8pt; color:#6b6b86; margin-top:4pt; }}
code {{ font-family:"SF Mono",Menlo,monospace; font-size:8.4pt; background:#f4f4f9;
  padding:1pt 3pt; border-radius:3pt; }}
pre {{ font-family:"SF Mono",Menlo,monospace; font-size:8.3pt; background:#f7f7fb;
  border:1pt solid #e4e4ed; border-radius:6pt; padding:8pt 10pt; margin:7pt 0;
  white-space:pre-wrap; line-height:1.5; }}

/* dossiers */
.dossier {{ border:1pt solid #e4e4ed; border-radius:8pt; padding:10pt 11pt; margin:0 0 8pt;
  page-break-inside:avoid; background:#fff; }}
.dhead {{ display:flex; align-items:flex-start; gap:9pt; }}
.dbadge {{ width:22pt; height:22pt; border-radius:6pt; background:#e6177f; color:#fff;
  display:grid; place-items:center; font-weight:800; font-size:10.5pt; flex:none; }}
.dname {{ flex:1; }}
.dmeta {{ font-size:7.9pt; color:#6b6b86; margin-top:2pt; }}
.dverdict {{ font-size:7.8pt; font-weight:700; padding:2.5pt 7pt; border-radius:20pt;
  flex:none; max-width:46mm; text-align:center; }}
.dverdict.good {{ background:#e3f6ed; color:#0a7c53; }}
.dverdict.warn {{ background:#fdf3dc; color:#8a6400; }}
.dverdict.bad {{ background:#fdeaef; color:#b3133f; }}
.dverdict.muted {{ background:#f0f0f5; color:#50506c; }}
.dstats {{ display:grid; grid-template-columns:repeat(6,1fr); gap:5pt; margin:9pt 0 8pt; }}
.st {{ background:#fafaff; border:1pt solid #ececf4; border-radius:5pt; padding:5pt 6pt; }}
.sl {{ font-size:6.6pt; text-transform:uppercase; letter-spacing:.5pt; color:#6b6b86; }}
.sv {{ font-size:11.5pt; font-weight:800; line-height:1.15; margin-top:1pt;
  font-variant-numeric:tabular-nums; }}
.ss {{ font-size:6.8pt; color:#8a8aa3; }}
.dcase {{ font-size:8.7pt; color:#3a3a56; margin:0; line-height:1.55; }}
</style></head><body>

<!-- ============ COVER ============ -->
<div class="cover">
  <div class="cmark"><div class="clogo">RR</div>
    <div><div style="font-weight:800;font-size:11pt">Rajasthan Royals</div>
    <div style="font-size:8.4pt;color:#b9bae0">SupeRR Selector · Season 2</div></div></div>
  <div class="ctitle">Identifying the Most<br>Reliable Players<br><span>Under Pressure</span></div>
  <div class="csub">A ball-by-ball pressure model built on {meta['deliveries']:,} deliveries,
    and the twenty players it says Rajasthan should back at the IPL 2027 auction.</div>
  <div class="cstats">
    <div class="cstat"><b>{meta['deliveries']/1000:.0f}k</b><span>Deliveries</span></div>
    <div class="cstat"><b>{meta['matches']}</b><span>Matches</span></div>
    <div class="cstat"><b>5</b><span>IPL seasons</span></div>
    <div class="cstat"><b>13</b><span>Model variants</span></div>
    <div class="cstat"><b>0.128</b><span>Brier score</span></div>
  </div>
  <div class="cfoot">Round 1 — Methodology &amp; Selection Report &nbsp;·&nbsp; IPL 2022–2026 and T20 Internationals</div>
</div>

<!-- ============ EXEC SUMMARY ============ -->
<div class="page-break"></div>
<div class="kicker">Executive summary</div>
<h2>Pressure is measurable. “Clutch” mostly is not.</h2>
<div class="rule"></div>
<p class="lede">We scored every delivery in the data pack on a continuous, role-relative
Pressure Index, then measured each player against what the situation normally yields rather
than against a raw average. Three findings shaped the model — and the third changed it
fundamentally.</p>

<div class="grid3">
  <div class="card"><div class="n">01</div>
    <h4>Pressure doesn’t slow batters down — it gets them out</h4>
    <p>Run rate moves {press['runrate_change_pct']:+.1f}% across pressure bands, but the
    dismissal rate <b>doubles (+{press['wkt_rate_rise_pct']:.0f}%)</b> and runs per dismissal
    fall <b>{press['rpd_drop_pct']:.0f}%</b>. Pressure charges a risk premium, not a scoring
    penalty. A metric built on strike rate cannot see it.</p></div>
  <div class="card"><div class="n">02</div>
    <h4>Pressure is role-relative, not a phase of the innings</h4>
    <p>A run of dots strangles the batter but is pressure the <em>bowler is applying</em>.
    We score every ball twice, once from each side. Making the build-up pillar asymmetric is
    what finally made the bowling signal behave.</p></div>
  <div class="card"><div class="n">03</div>
    <h4>Buy quality, not a reputation for bottle</h4>
    <p>Overall impact repeats across halves of the data (r&nbsp;=&nbsp;{relb['overall']['full_length_r']:.2f}).
    The clutch premium does not (r&nbsp;=&nbsp;{relb['clutch']['full_length_r']:.2f}). So we shrink each
    player’s pressure record toward <em>their own</em> standard, not the league’s.</p></div>
</div>

<div class="box"><h4>What this ranking is — and is not</h4>
<p class="small" style="margin:0">It identifies the players with the highest <b>expected output
when the Pressure Index is high</b>. It is not a temperament ranking. Because the clutch premium
barely repeats, a player with a glamorous highlight reel and ordinary underlying numbers is a
trap — and the model is built to say so.</p></div>

<h3>The selections</h3>
<div class="grid2">
<div>
<p class="small muted" style="margin-bottom:2pt"><b>Top 10 batters under pressure</b></p>
<table><thead><tr><th class="l">#</th><th class="l">Player</th><th>SupeRR</th>
<th>Press.</th><th>Clutch</th><th>SR</th><th>P.balls</th><th>Mat</th><th>SD</th></tr></thead>
<tbody>{bat_rows()}</tbody></table>
</div>
<div>
<p class="small muted" style="margin-bottom:2pt"><b>Top 10 bowlers under pressure</b></p>
<table><thead><tr><th class="l">#</th><th class="l">Player</th><th>SupeRR</th>
<th>Press.</th><th>Clutch</th><th>Econ</th><th>P.balls</th><th>Mat</th><th>SD</th></tr></thead>
<tbody>{bowl_rows()}</tbody></table>
</div>
</div>
<p class="small muted">Order is the <b>consensus across 13 modelling variants</b>, not a single
parameter choice. <b>SupeRR</b> is the baseline-run composite (50 = pool average), shown for
reference — which is why it is not perfectly monotonic with the consensus order.
<b>Press.</b> = runs added per pressure delivery. <b>SD</b> = standard deviation of the
player’s rank across variants; lower is more certain.</p>

<!-- ============ 1. PRESSURE DEFINITION ============ -->
<div class="page-break"></div>
<div class="kicker">Section 1</div>
<h2>Defining pressure</h2>
<div class="rule"></div>
<p>The brief left the definition to us. We made two structural choices up front.</p>
<p><b>Pressure is continuous, not a death-overs switch.</b> Treating overs 16–20 as “pressure”
and everything else as “not” discards the hardest ball of a collapsing powerplay and includes a
dead rubber’s final over. Every delivery is scored 0–100.</p>
<p><b>Pressure is role-relative.</b> The same delivery is agony for one player and opportunity
for the other, so we compute <code>PI_bat</code> and <code>PI_bowl</code> separately.</p>

<pre>PI = 0.40·Leverage + 0.25·Adversity + 0.20·Scarcity + 0.15·Build-up
     ×  knockout multiplier (1.08)</pre>

<table><thead><tr><th class="l">Pillar</th><th class="l" style="width:52pt">Weight</th>
<th class="l">What it captures and how it is computed</th></tr></thead><tbody>
<tr><td class="nm">Leverage</td><td style="text-align:left">40%</td>
<td style="text-align:left">How much this ball can swing the result. Expected |ΔWin Probability|
from one delivery, obtained by enumerating the eight possible outcomes (0/1/2/3/4/6, wicket,
extra) against their state-conditional probabilities.</td></tr>
<tr><td class="nm">Adversity</td><td style="text-align:left">25%</td>
<td style="text-align:left">How badly your own side is placed: <code>1 − WP(own team)</code>.
This is the pillar that makes pressure role-relative.</td></tr>
<tr><td class="nm">Scarcity</td><td style="text-align:left">20%</td>
<td style="text-align:left">How much batting resource is spent, read off a fitted
Duckworth–Lewis-style resource curve, so balls and wickets are priced on one scale.</td></tr>
<tr><td class="nm">Build-up</td><td style="text-align:left">15%</td>
<td style="text-align:left"><b>Asymmetric.</b> Dots and wickets for the batter; runs and
boundaries conceded for the bowler. A one-ball lag means a delivery is never scored using its
own outcome.</td></tr>
</tbody></table>

<p>Leverage carries the most weight because it is the one pillar derived from a fitted
statistical model; the other three capture cricketing texture a win-probability model alone
misses. A ball scoring <b>PI ≥ {meta['pressure_weights']['cut']}</b> is classified as a pressure
ball ({press['pressure_share_bat']*100:.1f}% of deliveries for batting,
{press['pressure_share_bowl']*100:.1f}% for bowling) — but that threshold is used for
<em>reporting only</em>. The ratings themselves use continuous weighting.</p>

<h3>Supporting models</h3>
<table><thead><tr><th class="l">Model</th><th class="l">Purpose</th><th class="l">Performance</th>
</tr></thead><tbody>
<tr><td class="nm">Chase win probability</td><td style="text-align:left">Leverage + adversity, 2nd innings</td>
<td style="text-align:left"><b>Brier {diag['models']['inn2']['brier']:.3f}</b>, log loss
{diag['models']['inn2']['log_loss']:.3f} (coin flip = 0.25). Calibration near-perfect across all ten deciles.</td></tr>
<tr><td class="nm">1st-innings win probability</td><td style="text-align:left">Same, 1st innings</td>
<td style="text-align:left">Brier {diag['models']['inn1']['brier']:.3f} — materially weaker (see Limitations).</td></tr>
<tr><td class="nm">Resource curve <code>R(balls, wkts)</code></td><td style="text-align:left">Scarcity + wicket cost</td>
<td style="text-align:left">DL-form <code>Z(1−e^−λb/Z)</code> fitted per wicket column, blended with
empirical cell means. Reproduces the actual mean first-innings total to within 0.5 runs (176.5 vs 176.0).</td></tr>
</tbody></table>
<p class="small muted">All models are hand-rolled on numpy/pandas — the logistic regression is
IRLS, the DL fit a refined grid search. No library defaults are hidden anywhere in the pipeline.</p>

<figure class="avoid"><img src="{img('f7_calibration.png')}" style="width:62%">
<figcaption>Chase win-probability calibration. Marker size is the number of deliveries in each
decile; points sit on the diagonal, so when the model says 30% teams win 30% of the time.</figcaption></figure>

<!-- ============ 2. MEASUREMENT ============ -->
<div class="page-break"></div>
<div class="kicker">Section 2</div>
<h2>Measuring performance</h2>
<div class="rule"></div>
<p>Strike rate and economy are the wrong currency: what a good ball is worth depends entirely on
the situation. We price everything in <b>runs above expectation</b>.</p>
<pre>batter impact = (runs − xRuns) − wicketCost × (out − xWicket)
bowler impact = (xRuns − runs) + wicketCost × (wicket − xWicket)</pre>
<ul style="font-size:9.4pt;margin:0 0 9pt;padding-left:15pt">
<li style="margin-bottom:4pt"><b>xRuns / xWicket</b> — what the average player manages in that
exact situation, from hierarchical empirical means over (context, phase, wickets in hand,
pressure band, pace/spin), falling back to coarser keys below 200 deliveries. Critically,
<b>the pressure band is part of the conditioning</b>: pressure balls are judged against pressure
norms, which stops the death overs flattering everyone who bats there.</li>
<li style="margin-bottom:4pt"><b>wicketCost</b> — the batting resource a dismissal destroys, read
off the resource curve: ~16 runs in the powerplay down to 2–4 at the death. Fully data-derived.</li>
<li>Run-outs are excluded from bowler credit, byes and leg-byes from bowler debit, and
non-striker dismissals from the striker’s record.</li></ul>

<h3>Rating construction — three deliberate choices</h3>
<div class="box"><h4>1 · Weight, don’t filter</h4>
<p class="small" style="margin:0">A hard PI ≥ 65 cut-off left only 66 batters with 100+ pressure
balls — too thin to rank on. Instead every delivery contributes with weight <code>u^1.5</code>
where <code>u = (PI − 45)/55</code>, so the estimate uses all {meta['deliveries']/1000:.0f}k balls
while still being dominated by the hard ones. Recency is applied on top
(<code>{meta['rating_params']['recency_decay']}^seasons-ago</code>), because this is an auction decision.</p></div>

<div class="box"><h4>2 · Shrink toward the player, not the league</h4>
<p class="small" style="margin:0 0 5pt">Because overall form repeats (r = {relb['overall']['full_length_r']:.2f})
and clutch does not (r = {relb['clutch']['full_length_r']:.2f}), the statistically correct prior for
a player’s pressure performance is <em>their own overall record</em>:</p>
<pre style="margin:0">overall_hat = shrink(overall impact, league mean, k = 782)
press_hat   = shrink(pressure impact, overall_hat, k = 245)</pre>
<p class="small" style="margin:5pt 0 0">Ballasts <code>k</code> are derived from measured split-half
reliability (<code>k = n̄(1−r)/r</code>), not chosen by taste. This is also what a good selector does
by instinct: assume a quality player will cope until their pressure record says otherwise, loudly
and repeatedly.</p></div>

<div class="box"><h4>3 · Let components earn their weight</h4>
<p class="small" style="margin:0 0 5pt">Each component’s base weight is scaled by the square root of
its measured reliability, then renormalised.</p>
<table style="margin:0"><thead><tr><th class="l">Component</th><th>Batting weight</th>
<th>Bowling weight</th></tr></thead><tbody>
<tr><td class="nm">Pressure estimate</td><td>{meta['rating_weights']['batting']['press']*100:.1f}%</td>
<td>{meta['rating_weights']['bowling']['press']*100:.1f}%</td></tr>
<tr><td class="nm">Match consistency</td><td>{meta['rating_weights']['batting']['consistency']*100:.1f}%</td>
<td>{meta['rating_weights']['bowling']['consistency']*100:.1f}%</td></tr>
<tr><td class="nm">Clutch premium</td><td>{meta['rating_weights']['batting']['clutch']*100:.1f}%</td>
<td>{meta['rating_weights']['bowling']['clutch']*100:.1f}%</td></tr>
</tbody></table>
<p class="small" style="margin:5pt 0 0">The weights differ by role <em>because the reliability differs
by role</em> — bowling consistency repeats (r = {rell['pos_rate']['full_length_r']:.2f}), batting
consistency does not (r = {relb['pos_rate']['full_length_r']:.2f}).</p></div>

<h3>Fair comparisons</h3>
<table><thead><tr><th class="l" style="width:88pt">Issue</th><th class="l">Treatment</th></tr></thead><tbody>
<tr><td class="nm">Opposition quality</td><td style="text-align:left">Teams graded on their own
league-wide record in the data (runs conceded per ball for attacks, runs scored for batting units),
split into volume-weighted terciles. A batter’s context is the attack he faced; a bowler’s is the
batting unit he bowled at. Runs against a weak attack carry a higher <code>xRuns</code> and are
discounted automatically.</td></tr>
<tr><td class="nm">IPL vs T20I</td><td style="text-align:left">Competition type is a dimension of the
expectation model (<code>ipl</code> / <code>t20i</code> / <code>dev</code>). Emerging-Teams and
Rising-Stars competitions are separated out.</td></tr>
<tr><td class="nm">Sample size</td><td style="text-align:left">Two-level empirical-Bayes shrinkage with
data-derived ballasts; effective sample size reported per player.</td></tr>
<tr><td class="nm">Eligibility</td><td style="text-align:left">≥90 pressure deliveries, ≥400 total
deliveries, ≥12 matches. Batters additionally require a median batting position ≤7 — a No. 8 who hits
well is a useful asset but not a top-10 <em>batter</em>.</td></tr>
<tr><td class="nm">Phase confounding</td><td style="text-align:left">Validated within-phase, not just
across the whole dataset (Section 3).</td></tr>
</tbody></table>
<p class="small muted"><b>Final pools: {meta['players_bat_pool']} eligible batters,
{meta['players_bowl_pool']} eligible bowlers.</b></p>

<!-- ============ 3. EVIDENCE ============ -->
<div class="page-break"></div>
<div class="kicker">Section 3</div>
<h2>Does the index actually measure pressure?</h2>
<div class="rule"></div>
<p class="lede">A pressure definition is only meaningful if performance demonstrably degrades as it
rises. Four tests: does output fall, does it survive controlling for phase, does it depend on any
single pillar, and does the shortlist hold up?</p>

<h3>Test 1 — Output degrades as PI rises</h3>
<figure class="avoid"><img src="{img('f1_bands.png')}">
<figcaption>The middle and right panels are the finding. Run rate is essentially flat because
high-pressure balls cluster where everyone is already swinging; what collapses is survival.</figcaption></figure>
<table><thead><tr><th class="l">PI band</th><th>Balls</th><th>Run rate</th><th>Wkts / 100</th>
<th>Runs per dismissal</th></tr></thead><tbody>{BANDS}</tbody></table>

<h3>Test 2 — The signal survives controlling for phase</h3>
<p>The obvious objection is that this merely measures “which over is it”. So we split deliveries into
top and bottom pressure terciles <em>within</em> each phase. The gap survives everywhere — and for
bowlers it only behaved once the build-up pillar was made asymmetric.</p>
<figure class="avoid"><img src="{img('f2_phase.png')}">
<figcaption>Batting output falls and bowling economy rises in every phase of the innings, including
the powerplay, where “death-overs pressure” cannot be the explanation.</figcaption></figure>

<div class="page-break"></div>
<h3>Test 3 — No single pillar carries the result</h3>
<p>Build-up is the pillar most at risk of flattering the result, because recent scoring autocorrelates
with the current ball — a slow pitch produces both. Removing it shrinks the gap by roughly a third but
does not remove it. <b>Leverage alone separates almost nothing outside the death overs</b>, which is
precisely why the index is a composite and not just a win-probability model.</p>
<figure class="avoid"><img src="{img('f3_robust.png')}">
<figcaption>Change in runs per dismissal, top vs bottom pressure tercile, within phase. The full index
separates hardest in every phase.</figcaption></figure>

<h3>Test 4 — Stability of the shortlist</h3>
<p>Thirteen variants: pressure floor 35/45/55, linear/convex/steep weighting, recency 0.60/0.78/1.00,
three component-weighting schemes, three alternative pillar balances, and a stricter eligibility bar.</p>
<div class="grid3">
  <div class="card"><div class="n">0.70–0.99</div><h4>Rank correlation</h4>
    <p>Between the baseline ranking and every alternative specification.</p></div>
  <div class="card"><div class="n">7.2 / 7.5</div><h4>Top-10 retained</h4>
    <p>Out of 10, for batters and bowlers respectively, averaged across variants.</p></div>
  <div class="card"><div class="n">13 / 13</div><h4>Tim David top-2</h4>
    <p>Bumrah, Rashid, Varun, Pathirana and Archer are top-10 eligible in all thirteen.</p></div>
</div>
<p class="small muted">The published order is the consensus — mean percentile position across variants —
with each player’s rank standard deviation shown alongside, so the reader can see which selections are
firm and which are marginal.</p>

<!-- ============ 4. THE BATTERS ============ -->
<div class="page-break"></div>
<div class="kicker">Section 4</div>
<h2>The ten batters</h2>
<div class="rule"></div>
<figure class="avoid"><img src="{img('f5_bat.png')}">
<figcaption>Hollow marker = the player’s calm standard; filled marker = output under pressure. Pink
means they lift when it tightens, amber means they dip.</figcaption></figure>
{''.join(dossier(p, 'bat') for p in BAT[:3])}

<div class="page-break"></div>
{''.join(dossier(p, 'bat') for p in BAT[3:7])}

<div class="page-break"></div>
{''.join(dossier(p, 'bat') for p in BAT[7:])}

<!-- ============ 5. THE BOWLERS ============ -->
<div class="page-break"></div>
<div class="kicker">Section 5</div>
<h2>The ten bowlers</h2>
<div class="rule"></div>
<figure class="avoid"><img src="{img('f6_bowl.png')}">
<figcaption>Only Narine and Rashid concede <em>fewer</em> runs per over under pressure than when calm.
For the rest, the gain shows up in wickets.</figcaption></figure>
{''.join(dossier(p, 'bowl') for p in BOWL[:3])}

<div class="page-break"></div>
{''.join(dossier(p, 'bowl') for p in BOWL[3:7])}

<div class="page-break"></div>
{''.join(dossier(p, 'bowl') for p in BOWL[7:])}

<!-- ============ 6. SQUAD FIT ============ -->
<div class="page-break"></div>
<div class="kicker">Section 6</div>
<h2>What this means for Rajasthan</h2>
<div class="rule"></div>
<p class="lede">Running the IPL 2026 Rajasthan squad through the same model gives an uncomfortable but
useful picture: one genuinely elite pressure performer, and a middle order sitting in the bottom half
of the pool.</p>

<table><thead><tr><th class="l">IPL 2026 squad member</th><th>Batting rank</th><th>SupeRR</th>
<th>Bowling rank</th><th>SupeRR</th></tr></thead><tbody>{squad_rows()}</tbody></table>
<p class="small muted">10 of 27 squad members clear the eligibility bar. The remainder — including
Yashasvi Jaiswal and Vaibhav Sooryavanshi — fall below 90 pressure deliveries. That is a statement
about sample size, not ability: Jaiswal rated inside the top five on an earlier, more permissive
threshold and is a develop-and-protect asset rather than a weakness.</p>

<div class="grid3">
  <div class="card"><div class="n">01</div><h4>Protect the asset</h4>
    <p>Archer is already a top-ten pressure bowler. Retain, and buy a second death option so he is not
    bowling every hard over alone.</p></div>
  <div class="card"><div class="n">02</div><h4>Buy one elite finisher</h4>
    <p>The largest single gap in the squad. Tim David is the clearest recommendation and a genuine
    outlier, not a marginal call.</p></div>
  <div class="card"><div class="n">03</div><h4>Don’t pay the clutch premium</h4>
    <p>Where two targets are close, take the one with the better overall record and the larger sample
    — that is the half of the signal that persists.</p></div>
</div>

<div class="box"><h4>Priority order at the auction</h4>
<p class="small" style="margin:0"><b>1.</b> Tim David — finisher, solves No. 5–6 outright.
<b>2.</b> Josh Hazlewood or Nathan Ellis — a death bowler to share Archer’s load; Ellis is the value
route. <b>3.</b> Shreyas Iyer or Tilak Varma — a top-four batter who can rebuild <em>and</em>
accelerate. <b>4.</b> Rinku Singh — domestic finishing depth at a lower price.
Avoid paying a premium for Andre Russell: his pressure record sits below his own baseline and his
rank is the least stable in either list.</p></div>

<!-- ============ 7. LIMITATIONS ============ -->
<div class="page-break"></div>
<div class="kicker">Section 7</div>
<h2>Reliability and limitations</h2>
<div class="rule"></div>
<p>Matches are dealt alternately by date into two halves. A metric that measures skill correlates
across them; one that measures variance does not. Spearman–Brown converts the half-sample correlation
to full-length reliability.</p>
<figure class="avoid"><img src="{img('f4_reliability.png')}" style="width:78%">
<figcaption>This single chart is why the model is built the way it is. If clutch were a durable trait we
would rank on it directly.</figcaption></figure>
<table><thead><tr><th class="l">Metric</th><th>Batting</th><th>Bowling</th><th>Verdict</th>
</tr></thead><tbody>{REL_ROWS}</tbody></table>

<h3>Known limitations</h3>
<ol style="font-size:9.4pt;padding-left:15pt;margin:0 0 10pt">
<li style="margin-bottom:4pt"><b>This is not a temperament ranking.</b> It says these twenty have the
highest expected output when PI is high. Reading it as “strongest nerve” over-reads the evidence.</li>
<li style="margin-bottom:4pt"><b>Pressure samples are small</b> even across five seasons. Error bars on
any individual estimate are wide — hence the consensus approach and the published rank swings.</li>
<li style="margin-bottom:4pt"><b>No scouting data:</b> injuries, fitness, contract status, auction
availability or age. Nor pitch and dew, which matter most in exactly the death-over situations the
model weights heaviest.</li>
<li style="margin-bottom:4pt"><b>First-innings pressure is weaker.</b> The chase model is strong
(Brier {diag['models']['inn2']['brier']:.3f}); the first-innings model much weaker
({diag['models']['inn1']['brier']:.3f}), because without a target the state is less informative.
Batters who do their best work <em>setting</em> totals are likely under-credited.</li>
<li style="margin-bottom:4pt"><b>Build-up partly measures conditions, not the player</b> — quantified
in Test 3 rather than buried.</li>
<li><b>Residual context bias</b> for players whose record sits almost entirely in one competition —
flagged per player in the dossiers.</li></ol>

<h3>Data integrity</h3>
<div class="grid3">
  <div class="card"><h4>Reconstruction check</h4>
    <p><b>{meta['recon_exact']} of {meta['recon_checked']}</b> matches reproduce the official result
    margin exactly from our rebuilt innings totals. The remainder are D/L-adjusted or abandoned, plus
    one wicket-count discrepancy.</p></div>
  <div class="card"><h4>A real bug, caught and fixed</h4>
    <p>Extras tagged <code>other</code> were being counted as legal deliveries, pushing 150 innings past
    120 balls and corrupting every downstream state. We re-anchored the ball count to the official over
    number, eliminating all impossible states.</p></div>
  <div class="card"><h4>The source file is truncated</h4>
    <p>It stops at exactly 201,000 rows, mid-innings. 16 matches in <code>matches.csv</code> have no
    deliveries and the final match is incomplete; all are excluded from model fitting.</p></div>
</div>

<h3>Reproducing this</h3>
<p class="small">Six ordered Python stages, numpy + pandas only.</p>
<pre>s1_states.py   rebuild the live match state behind every ball; validate against result strings
s2_models.py   resource curve, win probability, leverage
s3_pressure.py Pressure Index + validation
s4_ratings.py  expected runs, impact, shrinkage, ratings
s5_sensitivity.py  13-variant sweep and consensus ranking
s6_export.py   dashboard + report data bundle</pre>
<p class="small muted" style="margin-top:12pt">Rajasthan Royals · SupeRR Selector Season 2 · Round 1 —
Methodology &amp; Selection Report. Generated from the supplied data pack;
{meta['matches']} matches, {meta['deliveries']:,} deliveries.</p>

</body></html>"""

out = ROOT / "SupeRR_Selector_Report.html"
out.write_text(HTML)
print(f"html: {out}  ({out.stat().st_size/1024:.0f} KB)")
