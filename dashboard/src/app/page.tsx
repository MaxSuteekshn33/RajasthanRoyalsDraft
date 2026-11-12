"use client";
import { useState } from "react";
import Overview from "@/components/Overview";
import Methodology from "@/components/Methodology";
import Validation from "@/components/Validation";
import Rankings from "@/components/Rankings";
import Players from "@/components/Players";
import SquadFit from "@/components/SquadFit";
import Limits from "@/components/Limits";
import meta from "@/data/meta.json";

const TABS = [
  { id: "overview", label: "Overview", hint: "The headline" },
  { id: "method", label: "Methodology", hint: "Defining pressure" },
  { id: "validation", label: "Validation", hint: "Does it hold up?" },
  { id: "rankings", label: "Rankings", hint: "The top 10s" },
  { id: "players", label: "Player Lab", hint: "Drill into anyone" },
  { id: "squad", label: "RR Squad Fit", hint: "The auction plan" },
  { id: "limits", label: "Limitations", hint: "What we can't see" },
] as const;

type TabId = (typeof TABS)[number]["id"];

export default function Page() {
  const [tab, setTab] = useState<TabId>("overview");

  return (
    <div className="min-h-screen bg-ink">
      {/* backdrop */}
      <div
        className="pointer-events-none fixed inset-0 opacity-70"
        style={{
          background:
            "radial-gradient(900px 500px at 12% -5%, rgba(230,23,127,0.16), transparent 60%), radial-gradient(800px 500px at 95% 0%, rgba(78,168,242,0.10), transparent 55%)",
        }}
      />

      <div className="relative mx-auto flex max-w-[1500px] gap-7 px-5 py-6 lg:px-8">
        {/* sidebar */}
        <aside className="sticky top-6 hidden h-[calc(100vh-3rem)] w-[232px] shrink-0 flex-col lg:flex">
          <div className="mb-7 flex items-center gap-3">
            <div className="grid h-11 w-11 place-items-center rounded-xl bg-rr font-black text-white glow">
              RR
            </div>
            <div className="leading-tight">
              <div className="text-[15px] font-extrabold tracking-tight">
                SupeRR Selector
              </div>
              <div className="text-[11px] font-medium text-muted">
                Pressure Intelligence
              </div>
            </div>
          </div>

          <nav className="flex flex-col gap-1">
            {TABS.map((t) => (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                className={`group rounded-xl px-3.5 py-2.5 text-left transition ${
                  tab === t.id
                    ? "bg-rr/15 ring-1 ring-rr/40"
                    : "hover:bg-panel-2/60"
                }`}
              >
                <div
                  className={`text-[13.5px] font-bold ${
                    tab === t.id ? "text-rr-soft" : "text-text"
                  }`}
                >
                  {t.label}
                </div>
                <div className="text-[11px] text-muted">{t.hint}</div>
              </button>
            ))}
          </nav>

          <div className="mt-auto rounded-xl border border-line/70 p-3.5 text-[11px] leading-relaxed text-muted">
            <div className="font-bold text-text">Round 1 · Data Pack</div>
            {meta.matches} matches · {(meta.deliveries / 1000).toFixed(0)}k deliveries
            <br />
            IPL 2022–2026 + T20I
          </div>
        </aside>

        {/* mobile nav */}
        <div className="fixed inset-x-0 bottom-0 z-40 border-t border-line bg-ink/95 p-2 backdrop-blur lg:hidden">
          <div className="flex gap-1 overflow-x-auto">
            {TABS.map((t) => (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                className={`whitespace-nowrap rounded-lg px-3 py-2 text-[12px] font-bold ${
                  tab === t.id ? "bg-rr/20 text-rr-soft" : "text-muted"
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>
        </div>

        <main className="min-w-0 flex-1 pb-24 lg:pb-6">
          <div key={tab} className="fadein">
            {tab === "overview" && <Overview go={setTab} />}
            {tab === "method" && <Methodology />}
            {tab === "validation" && <Validation />}
            {tab === "rankings" && <Rankings />}
            {tab === "players" && <Players />}
            {tab === "squad" && <SquadFit />}
            {tab === "limits" && <Limits />}
          </div>
        </main>
      </div>
    </div>
  );
}
