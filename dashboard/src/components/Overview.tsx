"use client";
import { Card, SectionTitle, Stat, Pill, fmt, signed } from "./ui";
import meta from "@/data/meta.json";
import rankings from "@/data/rankings.json";
import diagnostics from "@/data/diagnostics.json";

const cb = rankings.consensus_batters as any[];
const cl = rankings.consensus_bowlers as any[];
const press = diagnostics.pressure as any;
const relBat = (diagnostics.ratings as any).reliability_batting.metrics;

export default function Overview({ go }: { go: (t: any) => void }) {
  const bands = press.batting_by_pi as any[];
  const lo = bands[0],
    hi = bands[bands.length - 1];

  return (
    <div className="space-y-7">
      {/* hero */}
      <Card className="relative overflow-hidden !p-0">
        <div
          className="absolute inset-0 opacity-90"
          style={{
            background:
              "linear-gradient(120deg, rgba(230,23,127,0.22), rgba(12,13,43,0.1) 45%, rgba(78,168,242,0.14))",
          }}
        />
        <div className="relative p-7 md:p-9">
          <div className="flex flex-wrap items-center gap-2">
            <Pill tone="rr">Rajasthan Royals · SupeRR Selector S2</Pill>
            <Pill tone="gold">Round 1 · IPL 2027 Auction</Pill>
          </div>
          <h1 className="mt-4 max-w-4xl text-[30px] font-extrabold leading-[1.1] tracking-tight md:text-[42px]">
            Pressure is measurable.
            <br />
            <span className="text-rr-soft">Clutch is mostly noise.</span>
          </h1>
          <p className="mt-4 max-w-3xl text-[15px] leading-relaxed text-muted">
            We scored all {meta.deliveries.toLocaleString()} deliveries in the data pack on a
            continuous <strong className="text-text">Pressure Index</strong>, then measured every
            player against what the situation normally yields. The headline finding reshaped the
            model: a player&apos;s <em className="text-text">overall</em> quality repeats across
            seasons, but their <em className="text-text">clutch premium</em> barely does. So we rank
            by expected performance under pressure — not by who got lucky in a few big moments.
          </p>
          <div className="mt-6 flex flex-wrap gap-2.5">
            <button
              onClick={() => go("rankings")}
              className="rounded-xl bg-rr px-4 py-2.5 text-[13px] font-bold text-white transition hover:brightness-110"
            >
              See the Top 10s →
            </button>
            <button
              onClick={() => go("method")}
              className="rounded-xl border border-line px-4 py-2.5 text-[13px] font-bold text-text transition hover:bg-panel-2"
            >
              How pressure is defined
            </button>
          </div>
        </div>
      </Card>

      {/* key numbers */}
      <div className="grid grid-cols-2 gap-3.5 md:grid-cols-4">
        <Stat
          label="Deliveries modelled"
          value={(meta.deliveries / 1000).toFixed(0) + "k"}
          sub={`${meta.matches} matches · ${meta.ipl_matches} IPL, ${meta.t20i_matches} T20I`}
        />
        <Stat
          label="Win-prob accuracy"
          value={fmt((diagnostics.models as any).inn2.brier, 3)}
          sub="Brier score on chases (0.25 = coin flip)"
          tone="mint"
        />
        <Stat
          label="Runs per dismissal"
          value={`${fmt(lo.runs_per_dismissal, 1)} → ${fmt(hi.runs_per_dismissal, 1)}`}
          sub="Lowest vs highest pressure band — batting gets 52% harder"
          tone="rr"
        />
        <Stat
          label="Clutch repeatability"
          value={fmt(relBat.clutch.full_length_r, 2)}
          sub="Split-half correlation for batters. Essentially zero."
          tone="gold"
        />
      </div>

      {/* the three findings */}
      <div>
        <SectionTitle
          kicker="What the data says"
          title="Three findings that drive every recommendation"
        />
        <div className="grid gap-3.5 md:grid-cols-3">
          {[
            {
              n: "01",
              t: "Pressure doesn't slow batters down — it gets them out",
              b: `Run rate barely moves across pressure bands (${signed(
                press.runrate_change_pct,
                1
              )}%), but the dismissal rate doubles (+${fmt(
                press.wkt_rate_rise_pct,
                0
              )}%). Pressure extracts a risk premium, not a scoring penalty. Any metric built on strike rate alone misses it entirely.`,
              tone: "rr" as const,
            },
            {
              n: "02",
              t: "Pressure is role-relative, not a phase of the innings",
              b: "A run of dots strangles the batter but is pressure the bowler is applying. We score each delivery twice — once from each side — which is what finally made the bowling signal behave.",
              tone: "sky" as const,
            },
            {
              n: "03",
              t: "Buy quality, not reputation for 'bottle'",
              b: `Overall impact repeats across halves of the data (r = ${fmt(
                relBat.overall.full_length_r,
                2
              )}). The clutch premium does not (r = ${fmt(
                relBat.clutch.full_length_r,
                2
              )}). We therefore shrink a player's pressure record toward their own standard, not the league's.`,
              tone: "gold" as const,
            },
          ].map((f) => (
            <Card key={f.n} className="flex flex-col">
              <div className="flex items-center gap-2.5">
                <span className="text-[22px] font-black text-line">{f.n}</span>
                <Pill tone={f.tone}>Finding</Pill>
              </div>
              <div className="mt-3 text-[15px] font-bold leading-snug">{f.t}</div>
              <p className="mt-2 text-[13px] leading-relaxed text-muted">{f.b}</p>
            </Card>
          ))}
        </div>
      </div>

      {/* top 10 preview */}
      <div className="grid gap-3.5 lg:grid-cols-2">
        {[
          { title: "Top 10 Batters Under Pressure", rows: cb, key: "striker_name" },
          { title: "Top 10 Bowlers Under Pressure", rows: cl, key: "bowler_name" },
        ].map((t) => (
          <Card key={t.title}>
            <div className="mb-3 flex items-center justify-between">
              <div className="text-[14px] font-extrabold">{t.title}</div>
              <Pill tone="line">consensus of 13 model variants</Pill>
            </div>
            <div className="space-y-1">
              {t.rows.slice(0, 10).map((r: any, i: number) => (
                <div
                  key={r[t.key]}
                  className="flex items-center gap-3 rounded-lg px-2 py-[7px] odd:bg-panel-2/40"
                >
                  <div
                    className={`grid h-6 w-6 shrink-0 place-items-center rounded-md text-[11px] font-black ${
                      i < 3 ? "bg-rr text-white" : "bg-line/60 text-muted"
                    }`}
                  >
                    {i + 1}
                  </div>
                  <div className="min-w-0 flex-1 truncate text-[13.5px] font-semibold">
                    {r[t.key]}
                  </div>
                  <div className="tnum text-[12px] text-muted">
                    top-{r.worst_rank} worst
                  </div>
                  <div className="tnum w-12 text-right text-[13px] font-bold text-rr-soft">
                    {(r.mean_pct * 100).toFixed(0)}
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-3 text-[11.5px] leading-relaxed text-muted">
              Score = mean percentile position across every modelling variant we tested.
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
