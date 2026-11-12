"use client";
import { useMemo, useState } from "react";
import {
  Bar as RBar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Card, SectionTitle, Pill, fmt, signed, CHART_AXIS, CHART_GRID } from "./ui";
import batsmen from "@/data/players_bat.json";
import bowlers from "@/data/players_bowl.json";

const axis = { stroke: CHART_AXIS, fontSize: 11 };
const tipStyle = {
  background: "#0c0d2b",
  border: "1px solid #262a63",
  borderRadius: 10,
  fontSize: 12,
};

type Role = "bat" | "bowl";
const SETS: Record<Role, any[]> = { bat: batsmen as any[], bowl: bowlers as any[] };

function Compare({ p }: { p: any }) {
  const isBat = p.role === "batter";
  const rows = isBat
    ? [
        { l: "Strike rate", a: p.pressure?.strike_rate, b: p.calm?.strike_rate, d: 1, up: true },
        {
          l: "Balls per dismissal",
          a: p.pressure?.balls_per_dismissal,
          b: p.calm?.balls_per_dismissal,
          d: 1,
          up: true,
        },
        { l: "Runs", a: p.pressure?.runs, b: p.calm?.runs, d: 0, up: true },
        { l: "Balls faced", a: p.pressure?.balls, b: p.calm?.balls, d: 0, up: true },
      ]
    : [
        { l: "Economy", a: p.pressure?.economy, b: p.calm?.economy, d: 2, up: false },
        {
          l: "Balls per wicket",
          a: p.pressure?.balls_per_wicket,
          b: p.calm?.balls_per_wicket,
          d: 1,
          up: false,
        },
        { l: "Wickets", a: p.pressure?.wickets, b: p.calm?.wickets, d: 0, up: true },
        { l: "Balls bowled", a: p.pressure?.balls, b: p.calm?.balls, d: 0, up: true },
      ];

  return (
    <div className="overflow-hidden rounded-xl border border-line">
      <div className="grid grid-cols-[1.3fr_1fr_1fr] bg-panel-2/60 px-3.5 py-2 text-[10.5px] font-bold uppercase tracking-wider text-muted">
        <span />
        <span className="text-right text-rr-soft">Under pressure</span>
        <span className="text-right">Calm</span>
      </div>
      {rows.map((r) => (
        <div
          key={r.l}
          className="grid grid-cols-[1.3fr_1fr_1fr] items-center border-t border-line/40 px-3.5 py-2.5 text-[13px]"
        >
          <span className="text-muted">{r.l}</span>
          <span className="tnum text-right font-bold text-text">{fmt(r.a, r.d)}</span>
          <span className="tnum text-right text-muted">{fmt(r.b, r.d)}</span>
        </div>
      ))}
    </div>
  );
}

export default function Players() {
  const [role, setRole] = useState<Role>("bat");
  const [q, setQ] = useState("");
  const list = SETS[role];
  const [sel, setSel] = useState<number>(list[0]?.id);

  const filtered = useMemo(
    () => list.filter((p) => p.name.toLowerCase().includes(q.toLowerCase())),
    [list, q]
  );
  const p = useMemo(
    () => list.find((x) => x.id === sel) ?? filtered[0] ?? list[0],
    [list, sel, filtered]
  );

  const PHASE_ORDER = ["1-6", "7-11", "12-15", "16-17", "18-20"];
  const phaseData = (p?.by_phase ?? [])
    .filter((x: any) => x.impact !== null)
    .sort(
      (a: any, b: any) => PHASE_ORDER.indexOf(a.phase) - PHASE_ORDER.indexOf(b.phase)
    )
    .map((x: any) => ({ phase: `Ov ${x.phase}`, impact: x.impact, balls: x.press_balls }));
  const seasonData = (p?.by_season ?? []).map((x: any) => ({
    season: x.season,
    impact: x.impact,
    balls: x.press_balls,
  }));

  return (
    <div className="space-y-6">
      <SectionTitle
        kicker="Player Lab"
        title="Drill into anyone in the pool"
        blurb="Every number traces back to the ball-by-ball file: how a player actually performed when the Pressure Index was high, versus when it was not."
      />

      <div className="flex flex-wrap items-center gap-2">
        {(["bat", "bowl"] as Role[]).map((r) => (
          <button
            key={r}
            onClick={() => {
              setRole(r);
              setSel(SETS[r][0]?.id);
            }}
            className={`rounded-xl px-4 py-2 text-[13px] font-bold transition ${
              role === r ? "bg-rr text-white" : "border border-line text-muted hover:bg-panel-2"
            }`}
          >
            {r === "bat" ? "Batters" : "Bowlers"}
          </button>
        ))}
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Search…"
          className="ml-auto rounded-lg border border-line bg-ink/60 px-3 py-1.5 text-[13px] outline-none placeholder:text-muted focus:border-rr"
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-[260px_1fr]">
        {/* list */}
        <Card className="!p-2 lg:max-h-[760px] lg:overflow-y-auto">
          {filtered.map((x) => (
            <button
              key={x.id}
              onClick={() => setSel(x.id)}
              className={`flex w-full items-center gap-2.5 rounded-lg px-2.5 py-2 text-left transition ${
                p?.id === x.id ? "bg-rr/15 ring-1 ring-rr/40" : "hover:bg-panel-2/60"
              }`}
            >
              <span className="tnum w-6 shrink-0 text-[11px] font-bold text-muted">
                {x.consensus_rank ?? x.rank}
              </span>
              <span className="min-w-0 flex-1 truncate text-[13px] font-semibold">{x.name}</span>
              <span className="tnum text-[12px] font-bold text-rr-soft">
                {fmt(x.superrr, 0)}
              </span>
            </button>
          ))}
        </Card>

        {/* profile */}
        {p && (
          <div key={p.id} className="fadein space-y-4">
            <Card>
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <Pill tone="rr">Consensus #{p.consensus_rank ?? "—"}</Pill>
                    <Pill tone="line">Baseline #{p.rank}</Pill>
                    {p.ipl_share > 0.5 ? (
                      <Pill tone="gold">IPL regular</Pill>
                    ) : (
                      <Pill tone="sky">
                        {(p.ipl_share * 100).toFixed(0)}% of balls in IPL
                      </Pill>
                    )}
                  </div>
                  <h3 className="mt-2 text-[27px] font-extrabold leading-none tracking-tight">
                    {p.name}
                  </h3>
                  <div className="mt-1.5 text-[12.5px] text-muted">
                    {p.teams.slice(0, 3).join(" · ")}
                    {p.bat_pos ? ` · bats ${p.bat_pos.toFixed(0)}` : ""}
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-[10.5px] uppercase tracking-widest text-muted">
                    SupeRR rating
                  </div>
                  <div className="tnum text-[40px] font-extrabold leading-none text-rr-soft">
                    {fmt(p.superrr, 1)}
                  </div>
                  <div className="text-[11px] text-muted">50 = pool average</div>
                </div>
              </div>

              <div className="mt-5 grid grid-cols-2 gap-2.5 md:grid-cols-4">
                {[
                  ["Pressure balls", p.press_balls, `of ${p.balls} total`],
                  ["Matches", p.matches, `last seen ${p.last_season}`],
                  [
                    "Pressure impact",
                    signed(p.impact_press),
                    "runs added per ball",
                  ],
                  ["Clutch Δ", signed(p.clutch), "pressure minus calm"],
                ].map(([l, v, s]) => (
                  <div key={l as string} className="rounded-xl border border-line bg-ink/40 p-3">
                    <div className="text-[10px] uppercase tracking-wider text-muted">{l}</div>
                    <div className="tnum mt-0.5 text-[19px] font-extrabold">{v as any}</div>
                    <div className="text-[10.5px] text-muted">{s}</div>
                  </div>
                ))}
              </div>
            </Card>

            <div className="grid gap-4 md:grid-cols-2">
              <Card>
                <div className="mb-3 text-[14px] font-extrabold">Pressure vs calm</div>
                <Compare p={p} />
                <p className="mt-3 text-[12px] leading-relaxed text-muted">
                  {p.clutch > 0.08
                    ? "Lifts measurably when the situation tightens."
                    : p.clutch < -0.08
                    ? "Numbers dip when the pressure comes on — the rating leans on overall quality."
                    : "Holds their normal standard when the game tightens, which is itself the point."}
                </p>
              </Card>

              <Card>
                <div className="mb-3 text-[14px] font-extrabold">
                  Pressure impact by phase
                </div>
                {phaseData.length ? (
                  <ResponsiveContainer width="100%" height={210}>
                    <BarChart data={phaseData} margin={{ top: 4, right: 8, bottom: 2, left: -18 }}>
                      <CartesianGrid stroke={CHART_GRID} strokeDasharray="3 3" vertical={false} />
                      <XAxis dataKey="phase" {...axis} />
                      <YAxis {...axis} tickFormatter={(v) => Number(v).toFixed(2)} />
                      <Tooltip
                        contentStyle={tipStyle}
                        formatter={(v: any) => [Number(v).toFixed(3), "Impact/ball"]}
                      />
                      <RBar dataKey="impact" radius={[4, 4, 0, 0]}>
                        {phaseData.map((e: any, i: number) => (
                          <Cell key={i} fill={e.impact >= 0 ? "#e6177f" : "#f2c14e"} />
                        ))}
                      </RBar>
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="py-10 text-center text-[13px] text-muted">
                    Not enough pressure balls per phase.
                  </div>
                )}
                <div className="text-[11px] text-muted">
                  Runs added per pressure delivery. Phases with fewer than 10 pressure balls are
                  hidden.
                </div>
              </Card>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <Card>
                <div className="mb-3 text-[14px] font-extrabold">Season trend</div>
                <ResponsiveContainer width="100%" height={200}>
                  <LineChart data={seasonData} margin={{ top: 6, right: 10, bottom: 2, left: -18 }}>
                    <CartesianGrid stroke={CHART_GRID} strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="season" {...axis} />
                    <YAxis {...axis} tickFormatter={(v) => Number(v).toFixed(2)} />
                    <Tooltip
                      contentStyle={tipStyle}
                      formatter={(v: any) => [Number(v).toFixed(3), "Impact/ball"]}
                    />
                    <Line
                      type="monotone"
                      dataKey="impact"
                      stroke="#e6177f"
                      strokeWidth={2.5}
                      dot={{ r: 3.5 }}
                      connectNulls
                    />
                  </LineChart>
                </ResponsiveContainer>
                <div className="text-[11px] text-muted">
                  Ratings weight recent seasons more heavily (decay{" "}
                  {0.78}<sup>seasons ago</sup>).
                </div>
              </Card>

              <Card>
                <div className="mb-3 text-[14px] font-extrabold">Signature performances</div>
                <div className="space-y-2">
                  {(p.moments ?? []).map((m: any, i: number) => (
                    <div key={i} className="rounded-xl border border-line bg-ink/40 p-3">
                      <div className="flex items-baseline justify-between gap-3">
                        <div className="text-[13px] font-bold">vs {m.opp}</div>
                        <div className="tnum text-[11px] text-muted">{m.date}</div>
                      </div>
                      <div className="mt-1 text-[12px] text-muted">
                        {p.role === "batter"
                          ? `${m.runs} off ${m.balls} · ${m.press_balls} under pressure`
                          : `${m.wkts} wkt · ${m.runs} runs off ${m.balls} · ${m.press_balls} under pressure`}
                      </div>
                      <div className="mt-1 truncate text-[11.5px] text-muted/80">{m.result}</div>
                    </div>
                  ))}
                  {!p.moments?.length && (
                    <div className="py-6 text-center text-[13px] text-muted">
                      No qualifying high-pressure games.
                    </div>
                  )}
                </div>
              </Card>
            </div>

            <Card>
              <div className="mb-3 text-[14px] font-extrabold">How stable is this rating?</div>
              <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
                {[
                  ["Variants eligible", `${p.scenarios_eligible ?? "—"}/13`],
                  ["Mean percentile", p.mean_pct ? (p.mean_pct * 100).toFixed(0) : "—"],
                  ["Rank swing", p.rank_sd ? `±${fmt(p.rank_sd, 1)}` : "—"],
                  ["Shrunk estimate", signed(p.press_hat)],
                ].map(([l, v]) => (
                  <div key={l as string} className="rounded-xl border border-line bg-ink/40 p-3">
                    <div className="text-[10px] uppercase tracking-wider text-muted">{l}</div>
                    <div className="tnum mt-0.5 text-[18px] font-extrabold">{v as any}</div>
                  </div>
                ))}
              </div>
              <p className="mt-3 text-[12px] leading-relaxed text-muted">
                Raw pressure impact of {signed(p.impact_press)} shrinks to{" "}
                {signed(p.press_hat)} once sample size is accounted for — the smaller the pressure
                sample, the harder it is pulled back toward this player&apos;s own overall standard
                of {signed(p.impact_all)}.
              </p>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}
