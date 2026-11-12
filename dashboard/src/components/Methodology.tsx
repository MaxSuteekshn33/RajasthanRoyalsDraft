"use client";
import { useMemo, useState } from "react";
import { Card, SectionTitle, Pill, fmt } from "./ui";
import meta from "@/data/meta.json";
import grid from "@/data/grid.json";

type Row = [number, number, number, number, number, number, number];
const GRID = grid as Row[];

const PILLARS = [
  {
    key: "Leverage",
    w: meta.pressure_weights.leverage,
    tone: "rr" as const,
    what: "How much this single ball can swing the result.",
    how: "We fit a win-probability model to every chase (Brier 0.128, near-perfect calibration), then enumerate the eight things a ball can do — 0,1,2,3,4,6, wicket, extra — against their state-conditional odds, and take the expected swing in win probability.",
  },
  {
    key: "Adversity",
    w: meta.pressure_weights.adversity,
    tone: "sky" as const,
    what: "How badly your own side is currently placed.",
    how: "One minus your team's win probability. This is the pillar that makes pressure role-relative: the same delivery is adversity for the batter and comfort for the bowler, so every ball is scored twice.",
  },
  {
    key: "Scarcity",
    w: meta.pressure_weights.scarcity,
    tone: "gold" as const,
    what: "How much batting resource has already been spent.",
    how: "Read straight off a Duckworth–Lewis-style resource curve we fitted to the data, so balls remaining and wickets in hand are priced on a single scale rather than treated separately.",
  },
  {
    key: "Build-up",
    w: meta.pressure_weights.buildup,
    tone: "mint" as const,
    what: "The squeeze applied over the previous 12 deliveries.",
    how: "Asymmetric by design. Dots and wickets strangle the batter; for the bowler the mirror image — boundaries and runs flowing — is what constitutes pressure. Computed with a one-ball lag so a delivery is never scored using its own outcome.",
  },
];

function nearest(bl: number, wl: number, need: number): Row | null {
  let best: Row | null = null;
  let bestD = Infinity;
  for (const r of GRID) {
    const d =
      Math.abs(r[0] - bl) * 2 + Math.abs(r[1] - wl) * 6 + Math.abs(r[2] - need);
    if (d < bestD) {
      bestD = d;
      best = r;
    }
  }
  return best;
}

function Gauge({ value, label, tone }: { value: number; label: string; tone: string }) {
  const pct = Math.max(0, Math.min(100, value));
  return (
    <div>
      <div className="mb-1.5 flex items-baseline justify-between">
        <span className="text-[11.5px] font-semibold text-muted">{label}</span>
        <span className="tnum text-[18px] font-extrabold" style={{ color: tone }}>
          {pct.toFixed(0)}
        </span>
      </div>
      <div className="h-2.5 w-full overflow-hidden rounded-full bg-line/50">
        <div
          className="h-full rounded-full transition-all duration-300"
          style={{ width: `${pct}%`, background: tone }}
        />
      </div>
    </div>
  );
}

export default function Methodology() {
  const [bl, setBl] = useState(12);
  const [wl, setWl] = useState(4);
  const [need, setNeed] = useState(25);

  const row = useMemo(() => nearest(bl, wl, need), [bl, wl, need]);
  const rrr = bl > 0 ? (need * 6) / bl : 0;

  return (
    <div className="space-y-7">
      <SectionTitle
        kicker="Methodology"
        title="What counts as pressure?"
        blurb="The brief left the definition to us. We treat pressure as continuous rather than a death-overs switch, and as role-relative rather than a property of the match. Four pillars, each scaled 0–1 across the whole dataset, combine into a Pressure Index on 0–100."
      />

      {/* formula */}
      <Card>
        <div className="flex flex-wrap items-center gap-2 text-[13.5px] font-bold">
          <span className="text-muted">PI</span>
          <span className="text-muted">=</span>
          {PILLARS.map((p, i) => (
            <span key={p.key} className="flex items-center gap-2">
              {i > 0 && <span className="text-muted">+</span>}
              <span className="rounded-lg border border-line bg-panel-2/60 px-2.5 py-1">
                <span className="text-gold">{p.w.toFixed(2)}</span> ×{" "}
                <span className="text-text">{p.key}</span>
              </span>
            </span>
          ))}
          <span className="text-muted">× knockout multiplier</span>
        </div>
        <p className="mt-3 text-[13px] leading-relaxed text-muted">
          Weights put most of the load on leverage — the one pillar derived from a fitted
          statistical model — while the other three capture the cricketing texture a win-probability
          model alone misses. A ball scoring {meta.pressure_weights.cut}+ is classified as a
          pressure ball for reporting; the ratings themselves use the continuous score, so no data
          is thrown away.
        </p>
      </Card>

      <div className="grid gap-3.5 md:grid-cols-2">
        {PILLARS.map((p) => (
          <Card key={p.key}>
            <div className="flex items-center justify-between">
              <div className="text-[15px] font-extrabold">{p.key}</div>
              <Pill tone={p.tone}>{(p.w * 100).toFixed(0)}% weight</Pill>
            </div>
            <div className="mt-2 text-[13.5px] font-semibold text-text">{p.what}</div>
            <p className="mt-1.5 text-[12.5px] leading-relaxed text-muted">{p.how}</p>
          </Card>
        ))}
      </div>

      {/* calculator */}
      <div>
        <SectionTitle
          kicker="Try it"
          title="Pressure calculator"
          blurb="Set a chase situation and read the model's view of it. Every number here comes from the pipeline itself — a precomputed grid of 5,180 chase states, not a re-implementation."
        />
        <Card>
          <div className="grid gap-7 lg:grid-cols-[1fr_1.1fr]">
            <div className="space-y-5">
              {[
                { l: "Balls remaining", v: bl, set: setBl, min: 6, max: 120, step: 6 },
                { l: "Wickets in hand", v: wl, set: setWl, min: 1, max: 10, step: 1 },
                { l: "Runs needed", v: need, set: setNeed, min: 5, max: 140, step: 5 },
              ].map((s) => (
                <div key={s.l}>
                  <div className="mb-2 flex items-baseline justify-between">
                    <span className="text-[12.5px] font-semibold text-muted">{s.l}</span>
                    <span className="tnum text-[20px] font-extrabold text-text">{s.v}</span>
                  </div>
                  <input
                    type="range"
                    min={s.min}
                    max={s.max}
                    step={s.step}
                    value={s.v}
                    onChange={(e) => s.set(Number(e.target.value))}
                    className="w-full accent-rr"
                  />
                </div>
              ))}
              <div className="rounded-xl border border-line bg-panel-2/40 p-3.5">
                <div className="text-[11.5px] font-semibold uppercase tracking-wider text-muted">
                  Required rate
                </div>
                <div className="tnum mt-1 text-[24px] font-extrabold text-gold">
                  {fmt(rrr, 2)} <span className="text-[13px] font-semibold text-muted">rpo</span>
                </div>
              </div>
            </div>

            <div className="space-y-5">
              {row ? (
                <>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="rounded-xl border border-line bg-panel-2/40 p-4">
                      <div className="text-[11px] font-semibold uppercase tracking-wider text-muted">
                        Chasing team win prob.
                      </div>
                      <div className="tnum mt-1 text-[30px] font-extrabold text-sky">
                        {(row[3] * 100).toFixed(0)}%
                      </div>
                    </div>
                    <div className="rounded-xl border border-line bg-panel-2/40 p-4">
                      <div className="text-[11px] font-semibold uppercase tracking-wider text-muted">
                        Leverage
                      </div>
                      <div className="tnum mt-1 text-[30px] font-extrabold text-gold">
                        {fmt(row[4], 1)}×
                      </div>
                      <div className="text-[11px] text-muted">vs an average delivery</div>
                    </div>
                  </div>

                  <div className="space-y-4 rounded-xl border border-line bg-panel-2/40 p-4">
                    <Gauge value={row[5]} label="Pressure on the BATTER" tone="#ff5aa8" />
                    <Gauge value={row[6]} label="Pressure on the BOWLER" tone="#4ea8f2" />
                    <p className="text-[12px] leading-relaxed text-muted">
                      {row[5] >= row[6]
                        ? "The batting side is behind the game — the burden sits with the batter."
                        : "The chase is ahead of the rate — it is the bowler who has to produce something."}{" "}
                      Both rise together as leverage climbs, which is why the last over of a tight
                      chase is punishing for everyone on the field.
                    </p>
                  </div>
                </>
              ) : (
                <div className="text-muted">No comparable state in the grid.</div>
              )}
            </div>
          </div>
        </Card>
      </div>

      {/* measurement */}
      <div>
        <SectionTitle
          kicker="Measurement"
          title="Scoring a delivery: runs above expectation"
          blurb="Strike rate and economy are the wrong currency, because what a good ball is worth depends entirely on the situation. We price everything in runs."
        />
        <div className="grid gap-3.5 md:grid-cols-2">
          <Card>
            <Pill tone="rr">Batter</Pill>
            <div className="mt-3 rounded-lg border border-line bg-ink/60 p-3.5 font-mono text-[12.5px] leading-relaxed">
              impact = (runs − <span className="text-gold">xRuns</span>)
              <br />
              <span className="ml-[62px]" />− <span className="text-sky">wicketCost</span> × (out −{" "}
              <span className="text-gold">xWicket</span>)
            </div>
            <p className="mt-3 text-[12.5px] leading-relaxed text-muted">
              <span className="text-gold">xRuns</span> and{" "}
              <span className="text-gold">xWicket</span> are what the average player manages in that
              exact situation — conditioned on phase, wickets in hand, pace or spin, the strength of
              the attack faced, and the pressure band itself. Judging pressure balls against
              pressure norms is what stops the death overs flattering everyone who bats there.
            </p>
          </Card>
          <Card>
            <Pill tone="sky">Wicket cost</Pill>
            <div className="mt-3 rounded-lg border border-line bg-ink/60 p-3.5 font-mono text-[12.5px] leading-relaxed">
              cost = R(balls, wkts) − R(balls, wkts−1)
            </div>
            <p className="mt-3 text-[12.5px] leading-relaxed text-muted">
              A wicket is worth whatever batting resource it destroys, read off the fitted resource
              curve. That ranges from roughly 16 runs in the powerplay down to 2–4 at the death,
              where there is little left to lose. Bowling is scored as the mirror image, with
              run-outs excluded from the bowler&apos;s credit and byes excluded from their debit.
            </p>
          </Card>
        </div>
      </div>

      {/* rating construction */}
      <Card>
        <SectionTitle
          kicker="Rating"
          title="From deliveries to a shortlist"
          blurb="Three deliberate choices, each forced on us by what the data would actually support."
        />
        <div className="grid gap-5 md:grid-cols-3">
          {[
            {
              t: "Weight, don't filter",
              b: `A hard cut-off left only 66 batters with 100+ pressure balls. Instead every delivery contributes with a weight set by its Pressure Index, so the estimate uses all ${(
                meta.deliveries / 1000
              ).toFixed(0)}k balls while still being dominated by the hard ones.`,
            },
            {
              t: "Shrink toward the player, not the league",
              b: "Because overall form repeats and clutch doesn't, a player's pressure record is pulled back toward their own overall standard. The amount of pull is set by measured split-half reliability, not taste.",
            },
            {
              t: "Let components earn their weight",
              b: `Each component's weight is scaled by its measured reliability. That is why batting ends up ${(
                meta.rating_weights.batting.press * 100
              ).toFixed(0)}% driven by the pressure estimate, while bowling spreads ${(
                meta.rating_weights.bowling.press * 100
              ).toFixed(0)}/${(meta.rating_weights.bowling.consistency * 100).toFixed(
                0
              )}/${(meta.rating_weights.bowling.clutch * 100).toFixed(
                0
              )} — bowling consistency does repeat, batting consistency does not.`,
            },
          ].map((x) => (
            <div key={x.t}>
              <div className="text-[14px] font-extrabold text-rr-soft">{x.t}</div>
              <p className="mt-1.5 text-[12.5px] leading-relaxed text-muted">{x.b}</p>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
