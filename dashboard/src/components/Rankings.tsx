"use client";
import { useMemo, useState } from "react";
import { Card, SectionTitle, Pill, Bar, fmt, signed } from "./ui";
import rankings from "@/data/rankings.json";
import sensitivity from "@/data/sensitivity.json";

type Role = "bat" | "bowl";

const DATA = {
  bat: {
    consensus: rankings.consensus_batters as any[],
    pool: rankings.batters as any[],
    nameKey: "striker_name",
    idKey: "striker_id",
    freq: sensitivity.batter_frequency as any[],
    label: "Batters",
  },
  bowl: {
    consensus: rankings.consensus_bowlers as any[],
    pool: rankings.bowlers as any[],
    nameKey: "bowler_name",
    idKey: "bowler_id",
    freq: sensitivity.bowler_frequency as any[],
    label: "Bowlers",
  },
};

const COLUMNS = [
  { k: "superrr", l: "SupeRR", d: 1, hint: "Composite rating, 50 = pool average" },
  { k: "press_hat", l: "Press. impact", d: 3, hint: "Estimated runs added per ball under pressure" },
  { k: "impact_press", l: "Raw press.", d: 3, hint: "Unshrunk pressure impact per ball" },
  { k: "impact_calm", l: "Calm", d: 3, hint: "Impact per ball in low-pressure situations" },
  { k: "clutch_raw", l: "Clutch Δ", d: 3, hint: "Pressure minus calm" },
  { k: "pos_rate", l: "Pos. games", d: 2, hint: "Share of games with a positive pressure contribution" },
  { k: "press_balls", l: "Press. balls", d: 0, hint: "Deliveries at PI ≥ 65" },
  { k: "matches", l: "Mat", d: 0, hint: "Matches in the dataset" },
];

export default function Rankings() {
  const [role, setRole] = useState<Role>("bat");
  const [sort, setSort] = useState("superrr");
  const [q, setQ] = useState("");
  const [scenario, setScenario] = useState("baseline");

  const d = DATA[role];
  const scenarios = sensitivity.scenarios as Record<string, any>;
  const scenarioList = Object.keys(scenarios);

  const pool = useMemo(() => {
    const rows = [...d.pool];
    rows.sort((a, b) => (b[sort] ?? -99) - (a[sort] ?? -99));
    return rows.filter((r) =>
      q ? String(r[d.nameKey]).toLowerCase().includes(q.toLowerCase()) : true
    );
  }, [d, sort, q]);

  const maxAbs = useMemo(
    () => Math.max(...d.pool.map((r) => Math.abs(r.press_hat ?? 0))) || 1,
    [d]
  );

  const scenarioNames: string[] =
    scenarios[scenario]?.[role === "bat" ? "batters" : "bowlers"] ?? [];
  const baselineNames: string[] =
    scenarios["baseline"]?.[role === "bat" ? "batters" : "bowlers"] ?? [];

  return (
    <div className="space-y-7">
      <SectionTitle
        kicker="Rankings"
        title="The ten we would back"
        blurb="Final order is a consensus across 13 modelling variants rather than one parameter choice — a player has to hold up under most reasonable definitions of pressure to finish near the top."
      />

      <div className="flex flex-wrap items-center gap-2">
        {(["bat", "bowl"] as Role[]).map((r) => (
          <button
            key={r}
            onClick={() => setRole(r)}
            className={`rounded-xl px-4 py-2 text-[13px] font-bold transition ${
              role === r ? "bg-rr text-white" : "border border-line text-muted hover:bg-panel-2"
            }`}
          >
            {DATA[r].label}
          </button>
        ))}
      </div>

      {/* podium */}
      <div className="grid gap-3.5 md:grid-cols-3">
        {d.consensus.slice(0, 3).map((p, i) => {
          const full = d.pool.find((x) => x[d.idKey] === p[d.idKey]);
          return (
            <Card key={p[d.idKey]} className={i === 0 ? "glow" : ""}>
              <div className="flex items-start justify-between">
                <div>
                  <div className="text-[11px] font-bold uppercase tracking-widest text-muted">
                    Rank {i + 1}
                  </div>
                  <div className="mt-1 text-[19px] font-extrabold leading-tight">
                    {p[d.nameKey]}
                  </div>
                </div>
                <div
                  className={`grid h-10 w-10 place-items-center rounded-xl text-[15px] font-black ${
                    i === 0 ? "bg-rr text-white" : "bg-line/60 text-text"
                  }`}
                >
                  {i + 1}
                </div>
              </div>
              <div className="mt-4 grid grid-cols-3 gap-2 text-center">
                {[
                  ["SupeRR", fmt(full?.superrr, 1)],
                  ["Press. balls", full?.press_balls ?? "—"],
                  ["Worst rank", `#${p.worst_rank}`],
                ].map(([l, v]) => (
                  <div key={l as string} className="rounded-lg border border-line bg-ink/40 py-2">
                    <div className="text-[10px] uppercase tracking-wider text-muted">{l}</div>
                    <div className="tnum text-[15px] font-extrabold">{v as any}</div>
                  </div>
                ))}
              </div>
              <div className="mt-3 flex items-center gap-2 text-[11.5px] text-muted">
                <Pill tone={p.rank_sd < 2 ? "mint" : p.rank_sd < 4 ? "gold" : "rr"}>
                  ±{fmt(p.rank_sd, 1)} rank sd
                </Pill>
                <span>across {p.scenarios} variants</span>
              </div>
            </Card>
          );
        })}
      </div>

      {/* consensus 1-10 */}
      <Card>
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <div className="text-[16px] font-extrabold">
            Consensus Top 10 — {d.label} under pressure
          </div>
          <Pill tone="line">rank 1 = highest rated</Pill>
        </div>
        <div className="space-y-1.5">
          {d.consensus.slice(0, 10).map((p, i) => {
            const full = d.pool.find((x) => x[d.idKey] === p[d.idKey]);
            return (
              <div
                key={p[d.idKey]}
                className="grid grid-cols-[28px_1fr_auto] items-center gap-3 rounded-lg px-2.5 py-2.5 odd:bg-panel-2/40 md:grid-cols-[28px_200px_1fr_auto]"
              >
                <div
                  className={`grid h-7 w-7 place-items-center rounded-lg text-[12px] font-black ${
                    i < 3 ? "bg-rr text-white" : "bg-line/60 text-muted"
                  }`}
                >
                  {i + 1}
                </div>
                <div className="min-w-0">
                  <div className="truncate text-[14px] font-bold">{p[d.nameKey]}</div>
                  <div className="text-[11px] text-muted">
                    {full?.press_balls} pressure balls · {full?.matches} matches
                  </div>
                </div>
                <div className="hidden md:block">
                  <Bar value={full?.press_hat ?? 0} max={maxAbs} />
                  <div className="mt-1 flex justify-between text-[10.5px] text-muted">
                    <span>raw {signed(full?.impact_press)}</span>
                    <span>clutch {signed(full?.clutch_raw)}</span>
                  </div>
                </div>
                <div className="text-right">
                  <div className="tnum text-[17px] font-extrabold text-rr-soft">
                    {fmt(full?.superrr, 1)}
                  </div>
                  <div className="text-[10.5px] text-muted">
                    best #{p.best_rank} · worst #{p.worst_rank}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </Card>

      {/* scenario explorer */}
      <Card>
        <div className="mb-1 text-[16px] font-extrabold">
          Would a different analyst pick the same ten?
        </div>
        <p className="mb-4 max-w-3xl text-[13px] leading-relaxed text-muted">
          Switch the modelling choice and watch the list move. Names in pink drop out of the
          baseline top ten; names in green are new arrivals. Across all variants we retain{" "}
          <strong className="text-text">7.2/10 batters</strong> and{" "}
          <strong className="text-text">7.5/10 bowlers</strong>, with rank correlations of 0.70–0.99.
        </p>
        <div className="mb-4 flex flex-wrap gap-1.5">
          {scenarioList.map((s) => (
            <button
              key={s}
              onClick={() => setScenario(s)}
              className={`rounded-lg px-2.5 py-1.5 text-[11.5px] font-semibold transition ${
                scenario === s
                  ? "bg-sky/20 text-sky ring-1 ring-sky/50"
                  : "border border-line text-muted hover:bg-panel-2"
              }`}
            >
              {s}
            </button>
          ))}
        </div>
        <div className="grid gap-2 md:grid-cols-2">
          {scenarioNames.map((n, i) => {
            const isNew = !baselineNames.includes(n);
            return (
              <div
                key={n}
                className={`flex items-center gap-2.5 rounded-lg border px-3 py-2 text-[13px] ${
                  isNew ? "border-mint/40 bg-mint/5" : "border-line"
                }`}
              >
                <span className="tnum w-5 text-[11px] font-bold text-muted">{i + 1}</span>
                <span className="font-semibold">{n}</span>
                {isNew && <Pill tone="mint">new</Pill>}
              </div>
            );
          })}
        </div>
        {scenario !== "baseline" && (
          <div className="mt-3 flex flex-wrap gap-2">
            {baselineNames
              .filter((n) => !scenarioNames.includes(n))
              .map((n) => (
                <span
                  key={n}
                  className="rounded-lg border border-rr/40 bg-rr/5 px-2.5 py-1 text-[12px] text-rr-soft line-through"
                >
                  {n}
                </span>
              ))}
          </div>
        )}
      </Card>

      {/* full pool */}
      <Card>
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <div className="text-[16px] font-extrabold">
            Full eligible pool ({d.pool.length})
          </div>
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search player…"
            className="rounded-lg border border-line bg-ink/60 px-3 py-1.5 text-[13px] outline-none placeholder:text-muted focus:border-rr"
          />
        </div>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[820px] text-[12.5px]">
            <thead>
              <tr className="border-b border-line text-left text-[10.5px] uppercase tracking-wider text-muted">
                <th className="pb-2 pr-2">#</th>
                <th className="pb-2 pr-2">Player</th>
                {COLUMNS.map((c) => (
                  <th
                    key={c.k}
                    title={c.hint}
                    onClick={() => setSort(c.k)}
                    className={`cursor-pointer pb-2 pr-2 text-right transition hover:text-text ${
                      sort === c.k ? "text-rr-soft" : ""
                    }`}
                  >
                    {c.l}
                    {sort === c.k ? " ▾" : ""}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="tnum">
              {pool.map((r, i) => (
                <tr key={r[d.idKey]} className="border-b border-line/30 hover:bg-panel-2/40">
                  <td className="py-2 pr-2 text-muted">{i + 1}</td>
                  <td className="py-2 pr-2 font-semibold text-text">{r[d.nameKey]}</td>
                  {COLUMNS.map((c) => (
                    <td
                      key={c.k}
                      className={`py-2 pr-2 text-right ${
                        c.k === "superrr" ? "font-bold text-rr-soft" : ""
                      }`}
                    >
                      {c.k === "clutch_raw" ? signed(r[c.k], c.d) : fmt(r[c.k], c.d)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="mt-3 text-[11.5px] leading-relaxed text-muted">
          Eligibility: ≥90 pressure deliveries, ≥400 total deliveries, ≥12 matches, and — for
          batters — a median batting position of 7 or higher up the order. Click any column to sort.
        </div>
      </Card>
    </div>
  );
}
