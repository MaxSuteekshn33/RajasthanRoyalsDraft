"use client";
import { useState } from "react";
import { Card, SectionTitle, Pill, fmt, signed } from "./ui";
import squad from "@/data/squad.json";
import rankings from "@/data/rankings.json";

const S = squad as any;
const rated = S.squad.filter((p: any) => p.bat_rank || p.bowl_rank);
const unrated = S.squad.filter((p: any) => !p.bat_rank && !p.bowl_rank);

const RATIONALE: Record<string, string> = {
  "Tim David":
    "The single most valuable pressure asset in the dataset and the one name that survives all 13 model variants at the top. Strike rate actually rises under pressure (187 vs 173) while he survives longer than peers in the same situations. Solves RR's No. 5–6 problem outright.",
  "Namboori Tilak Varma":
    "Most pressure deliveries faced of any batter in the pool — 440 — and still well above expectation across them. Young, Indian, and the rare left-hander who can both rebuild and finish, which gives RR flexibility they currently lack.",
  "Shreyas Iyer":
    "The biggest positive gap between pressure and calm output of any top-ranked batter. Captaincy experience plus a proven ability to bat through a collapse — the exact failure mode RR's middle order showed.",
  "Suryakumar Yadav":
    "Elite in both regimes rather than a specialist, with the second-largest pressure sample in the pool. The safest high-floor pick on the board if RR want certainty over upside.",
  "Heinrich Klaasen":
    "Pressure impact well clear of his calm baseline and a wicketkeeping option, which would let RR carry an extra bowler. Overseas slot is the only constraint.",
  "Jos Buttler":
    "Returns the highest share of games with a positive pressure contribution in the entire batting pool. Knows the franchise. A sentimental pick that the numbers happen to endorse.",
  "Josh Hazlewood":
    "Top-rated bowler under pressure on the consensus and the best raw pressure impact in the pool. Relentlessly repeatable at the death — the perfect foil at the other end to Archer.",
  "Nathan Ellis":
    "Specialist death bowler whose entire value is concentrated exactly where the Pressure Index is highest. Likely to go for a fraction of the marquee names.",
  "Jasprit Bumrah":
    "Best overall bowling impact in the dataset, and it barely moves when pressure arrives — he simply is this good all the time. The most expensive route to the same outcome.",
  "Sunil Narine":
    "Spin that holds its economy under pressure in the powerplay as well as the middle, plus genuine top-order batting value. Two squad slots for one.",
  "Rashid Khan":
    "Largest pressure sample of any spinner and consistently positive across 13 variants. The benchmark for a wicket-taking middle-overs option.",
  "Matheesha Pathirana":
    "Elite overall impact with a slingy action that is hardest to line up precisely when batters must take risks. Young enough to be a multi-season asset.",
  "Varun Chakravarthy":
    "Mystery spin that keeps taking wickets as pressure rises rather than going defensive. Covers RR's middle-overs strike-bowling gap.",
  "Eshan Malinga":
    "The value pick. Clear positive clutch delta on a smaller sample, and unlikely to attract a bidding war.",
};

export default function SquadFit() {
  const [tab, setTab] = useState<"bat" | "bowl">("bat");
  const targets = tab === "bat" ? S.targets_bat : S.targets_bowl;
  const nameKey = tab === "bat" ? "striker_name" : "bowler_name";
  const poolSize = tab === "bat" ? rankings.batters.length : rankings.bowlers.length;

  const bestBat = rated.reduce(
    (m: any, p: any) => (p.bat_rank && (!m || p.bat_rank < m.bat_rank) ? p : m),
    null
  );
  const bestBowl = rated.reduce(
    (m: any, p: any) => (p.bowl_rank && (!m || p.bowl_rank < m.bowl_rank) ? p : m),
    null
  );

  return (
    <div className="space-y-7">
      <SectionTitle
        kicker="RR Squad Fit"
        title="Where the Royals actually need help"
        blurb="Running the IPL 2026 Rajasthan squad through the same model gives an uncomfortable but useful picture: one genuinely elite pressure performer, and a middle order that sits in the bottom half of the pool."
      />

      {/* diagnosis */}
      <div className="grid gap-3.5 md:grid-cols-3">
        <Card className="glow">
          <Pill tone="mint">Strength</Pill>
          <div className="mt-2.5 text-[17px] font-extrabold">{bestBowl?.name}</div>
          <div className="tnum mt-1 text-[13px] text-muted">
            Bowling rank #{bestBowl?.bowl_rank} of {bestBowl?.bowl_pool} · SupeRR{" "}
            {fmt(bestBowl?.bowl_superrr, 1)}
          </div>
          <p className="mt-3 text-[12.5px] leading-relaxed text-muted">
            Already contracted and already top-ten in the world under pressure. The squad plan
            should be built around protecting and partnering him, not replacing him.
          </p>
        </Card>
        <Card>
          <Pill tone="gold">Gap</Pill>
          <div className="mt-2.5 text-[17px] font-extrabold">
            No top-15 pressure batter
          </div>
          <div className="tnum mt-1 text-[13px] text-muted">
            Best is {bestBat?.name} at #{bestBat?.bat_rank} of {bestBat?.bat_pool}
          </div>
          <p className="mt-3 text-[12.5px] leading-relaxed text-muted">
            Hetmyer, Jadeja, Jurel and Curran all sit in the bottom half of the eligible batting
            pool for pressure impact. When RR lose early wickets in a chase, the model expects the
            innings to fold.
          </p>
        </Card>
        <Card>
          <Pill tone="sky">Priority</Pill>
          <div className="mt-2.5 text-[17px] font-extrabold">One finisher, one death bowler</div>
          <p className="mt-3 text-[12.5px] leading-relaxed text-muted">
            The marginal rupee buys most where the Pressure Index is highest — overs 16–20 of a
            chase. A top-rated finisher plus a specialist death bowler to share the load with Archer
            addresses both failure modes RR showed.
          </p>
        </Card>
      </div>

      {/* current squad */}
      <Card>
        <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
          <div className="text-[16px] font-extrabold">
            IPL 2026 Rajasthan Royals squad, rated
          </div>
          <Pill tone="line">{rated.length} of {S.squad.length} meet the eligibility bar</Pill>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[520px] text-[13px]">
            <thead>
              <tr className="border-b border-line text-left text-[10.5px] uppercase tracking-wider text-muted">
                <th className="pb-2">Player</th>
                <th className="pb-2 text-right">Batting rank</th>
                <th className="pb-2 text-right">SupeRR</th>
                <th className="pb-2 text-right">Bowling rank</th>
                <th className="pb-2 text-right">SupeRR</th>
              </tr>
            </thead>
            <tbody className="tnum">
              {rated.map((p: any) => (
                <tr key={p.id} className="border-b border-line/30">
                  <td className="py-2 font-semibold text-text">{p.name}</td>
                  <td className="py-2 text-right">
                    {p.bat_rank ? (
                      <span className={p.bat_rank <= 15 ? "text-mint" : "text-muted"}>
                        #{p.bat_rank}/{p.bat_pool}
                      </span>
                    ) : (
                      <span className="text-line">—</span>
                    )}
                  </td>
                  <td className="py-2 text-right">{fmt(p.bat_superrr, 1)}</td>
                  <td className="py-2 text-right">
                    {p.bowl_rank ? (
                      <span className={p.bowl_rank <= 15 ? "text-mint" : "text-muted"}>
                        #{p.bowl_rank}/{p.bowl_pool}
                      </span>
                    ) : (
                      <span className="text-line">—</span>
                    )}
                  </td>
                  <td className="py-2 text-right">{fmt(p.bowl_superrr, 1)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="mt-3 text-[11.5px] leading-relaxed text-muted">
          {unrated.length} squad members — including Yashasvi Jaiswal and Vaibhav Sooryavanshi —
          fall below the 90-pressure-ball eligibility bar. That is a statement about sample size,
          not ability: Jaiswal rated inside the top five on an earlier, more permissive threshold
          and is flagged as a develop-and-protect asset rather than a weakness.
        </p>
      </Card>

      {/* targets */}
      <div>
        <div className="mb-4 flex flex-wrap items-center gap-2">
          {(["bat", "bowl"] as const).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`rounded-xl px-4 py-2 text-[13px] font-bold transition ${
                tab === t ? "bg-rr text-white" : "border border-line text-muted hover:bg-panel-2"
              }`}
            >
              {t === "bat" ? "Batting targets" : "Bowling targets"}
            </button>
          ))}
        </div>

        <div className="grid gap-3.5 md:grid-cols-2">
          {targets.slice(0, 6).map((t: any, i: number) => (
            <Card key={t[nameKey]}>
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <Pill tone={i === 0 ? "rr" : "line"}>
                      Target #{t.consensus_rank ?? i + 1}
                    </Pill>
                    {t.ipl_balls / t.balls > 0.5 ? (
                      <Pill tone="gold">IPL-proven</Pill>
                    ) : (
                      <Pill tone="sky">mostly T20I evidence</Pill>
                    )}
                  </div>
                  <div className="mt-2 text-[18px] font-extrabold leading-tight">
                    {t[nameKey]}
                  </div>
                </div>
                <div className="text-right">
                  <div className="tnum text-[26px] font-extrabold leading-none text-rr-soft">
                    {fmt(t.superrr, 1)}
                  </div>
                  <div className="text-[10.5px] text-muted">of {poolSize} eligible</div>
                </div>
              </div>

              <div className="mt-3 grid grid-cols-4 gap-2 text-center">
                {[
                  ["Press.", signed(t.impact_press, 2)],
                  ["Calm", signed(t.impact_calm, 2)],
                  ["Clutch", signed(t.clutch_raw, 2)],
                  ["Balls", t.press_balls],
                ].map(([l, v]) => (
                  <div key={l as string} className="rounded-lg border border-line bg-ink/40 py-1.5">
                    <div className="text-[9.5px] uppercase tracking-wider text-muted">{l}</div>
                    <div className="tnum text-[13px] font-bold">{v as any}</div>
                  </div>
                ))}
              </div>

              <p className="mt-3 text-[12.5px] leading-relaxed text-muted">
                {RATIONALE[t[nameKey]] ??
                  "Rates clearly above the pool average for expected performance under pressure and holds position across modelling variants."}
              </p>
            </Card>
          ))}
        </div>
      </div>

      {/* the plan */}
      <Card>
        <SectionTitle
          kicker="The plan"
          title="How we would spend at the IPL 2027 auction"
        />
        <div className="grid gap-5 md:grid-cols-3">
          {[
            {
              h: "1 · Protect the asset",
              b: "Archer is already a top-ten pressure bowler in the world. Retain, and buy a second death option so he is not bowling every hard over alone — the model shows economy degrading fastest for bowlers carrying the whole death burden.",
              tone: "mint" as const,
            },
            {
              h: "2 · Buy one elite finisher",
              b: "The largest single gap in the squad. Tim David is the model's clearest recommendation and is a genuine outlier rather than a marginal call — rank 1 or 2 in every one of the 13 variants.",
              tone: "rr" as const,
            },
            {
              h: "3 · Don't pay the clutch premium",
              b: "Because clutch barely repeats, a player with a glamorous highlight reel and ordinary underlying numbers is a trap. Where two targets are close, take the one with the better overall record and the larger sample — that is the half of the signal that persists.",
              tone: "gold" as const,
            },
          ].map((x) => (
            <div key={x.h}>
              <Pill tone={x.tone}>{x.h}</Pill>
              <p className="mt-2.5 text-[12.5px] leading-relaxed text-muted">{x.b}</p>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
