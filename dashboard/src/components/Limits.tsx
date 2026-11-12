"use client";
import { Card, SectionTitle, Pill, fmt } from "./ui";
import meta from "@/data/meta.json";
import diagnostics from "@/data/diagnostics.json";

const relBat = (diagnostics.ratings as any).reliability_batting.metrics;

const LIMITS = [
  {
    t: "Clutch is weakly repeatable — by design we lean on quality",
    b: `Split-half reliability for the clutch premium is ${fmt(
      relBat.clutch.full_length_r,
      2
    )} for batters. We report it and give it a small weight because the brief asks about rising to the occasion, but anyone reading this ranking as "these ten have the strongest temperament" is over-reading it. It says: these ten have the highest expected output when the Pressure Index is high.`,
    tone: "rr" as const,
  },
  {
    t: "Pressure samples are small even across five seasons",
    b: "Only 66 batters faced 100+ deliveries at PI ≥ 65. Continuous weighting recovers much of the lost precision, but the error bars on any individual pressure estimate remain wide. This is why the final order is a consensus across 13 variants rather than a single run, and why rank swing is published next to every name.",
    tone: "gold" as const,
  },
  {
    t: "The index cannot see the things a scout sees",
    b: "No data on injuries, fitness, contract status, auction availability, age, or whether a player was batting through a niggle. Nor on pitch and dew, which matter enormously in exactly the death-over situations the model weights most heavily. Venue appears only indirectly, through opposition strength.",
    tone: "sky" as const,
  },
  {
    t: "IPL and T20I are not the same competition",
    b: `Expectations are conditioned on competition type and on data-derived opposition strength tiers, so runs against a weaker attack are discounted. Residual bias remains for players whose record is concentrated in one context — flagged on each target card as "IPL-proven" or "mostly T20I evidence".`,
    tone: "mint" as const,
  },
  {
    t: "Build-up partly measures the conditions, not the player",
    b: "Recent dots and boundaries autocorrelate with the current ball — a slow pitch produces both. Stripping the pillar out shrinks the measured pressure gap by roughly a third but does not remove it, which is reported in full on the Validation tab rather than buried.",
    tone: "gold" as const,
  },
  {
    t: "First-innings pressure is intrinsically harder to pin down",
    b: `Our chase win-probability model is strong (Brier ${fmt(
      (diagnostics.models as any).inn2.brier,
      3
    )}); the first-innings model is much weaker (${fmt(
      (diagnostics.models as any).inn1.brier,
      3
    )}), because without a target the game state is far less informative. First-innings leverage is therefore flatter, and batters who do their best work setting totals are likely under-credited.`,
    tone: "sky" as const,
  },
];

export default function Limits() {
  return (
    <div className="space-y-7">
      <SectionTitle
        kicker="Reliability & limitations"
        title="Where this model is least certain"
        blurb="Everything below is a reason to treat the ranking as a shortlist for the room to argue over, not a verdict. We would rather hand a selector an honest ±3 than a confident single number."
      />

      <div className="grid gap-3.5 md:grid-cols-2">
        {LIMITS.map((l) => (
          <Card key={l.t}>
            <Pill tone={l.tone}>Caveat</Pill>
            <div className="mt-2.5 text-[15px] font-bold leading-snug">{l.t}</div>
            <p className="mt-2 text-[12.5px] leading-relaxed text-muted">{l.b}</p>
          </Card>
        ))}
      </div>

      <Card>
        <div className="text-[16px] font-extrabold">Data integrity checks we ran</div>
        <div className="mt-4 grid gap-4 md:grid-cols-3">
          {[
            {
              h: "Reconstruction vs official results",
              b: `We rebuilt every innings total from the deliveries and compared to the result string: ${meta.recon_exact} of ${meta.recon_checked} reproduce the official margin exactly. The rest are D/L-adjusted or abandoned games, plus one wicket-count discrepancy.`,
            },
            {
              h: "A mis-tagged extra, caught and fixed",
              b: `"other" extras were being counted as legal deliveries, pushing 150 innings past 120 balls and corrupting every downstream state. We re-anchored the ball count to the official over number, which eliminated all impossible states.`,
            },
            {
              h: "Truncated source file",
              b: `The supplied ball-by-ball file stops at exactly 201,000 rows, mid-innings. 16 matches listed in matches.csv have no deliveries, and the final match is incomplete; all are excluded from model fitting.`,
            },
          ].map((x) => (
            <div key={x.h}>
              <div className="text-[13.5px] font-bold text-rr-soft">{x.h}</div>
              <p className="mt-1.5 text-[12.5px] leading-relaxed text-muted">{x.b}</p>
            </div>
          ))}
        </div>
      </Card>

      <Card>
        <div className="text-[16px] font-extrabold">Reproducing this</div>
        <p className="mt-2 max-w-3xl text-[13px] leading-relaxed text-muted">
          The pipeline is six ordered Python stages running on numpy and pandas alone — the logistic
          regression, the Duckworth–Lewis-style resource fit and the shrinkage are all hand-rolled,
          so every coefficient is inspectable and nothing depends on a library default.
        </p>
        <div className="mt-4 grid gap-2 md:grid-cols-3">
          {[
            ["s1_states.py", "Rebuild the live match state behind every ball"],
            ["s2_models.py", "Resource curve, win probability, leverage"],
            ["s3_pressure.py", "Pressure Index + validation"],
            ["s4_ratings.py", "Expected runs, impact, shrinkage, ratings"],
            ["s5_sensitivity.py", "13-variant sweep and consensus ranking"],
            ["s6_export.py", "Everything this dashboard renders"],
          ].map(([f, d]) => (
            <div
              key={f}
              className="rounded-xl border border-line bg-ink/40 p-3"
            >
              <div className="font-mono text-[12px] font-bold text-gold">{f}</div>
              <div className="mt-1 text-[11.5px] leading-snug text-muted">{d}</div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
