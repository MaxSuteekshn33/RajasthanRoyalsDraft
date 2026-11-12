"use client";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from "recharts";
import { Card, SectionTitle, Pill, fmt, CHART_AXIS, CHART_GRID } from "./ui";
import diagnostics from "@/data/diagnostics.json";

const press = diagnostics.pressure as any;
const models = diagnostics.models as any;
const relBat = (diagnostics.ratings as any).reliability_batting.metrics;
const relBowl = (diagnostics.ratings as any).reliability_bowling.metrics;

const axis = { stroke: CHART_AXIS, fontSize: 11 };
const tipStyle = {
  background: "#0c0d2b",
  border: "1px solid #262a63",
  borderRadius: 10,
  fontSize: 12,
};

export default function Validation() {
  const bands = press.batting_by_pi as any[];
  const wphase = press.batting_within_phase as any[];
  const wbowl = press.bowling_within_phase as any[];
  const rob = press.robustness as any;

  const phaseOrder = ["1-6", "7-11", "12-15", "16-17", "18-20"];
  const phaseData = phaseOrder.map((p) => {
    const hi = wphase.find((r) => r.ovb === p && r.terc === "high");
    const lo = wphase.find((r) => r.ovb === p && r.terc === "low");
    const bhi = wbowl.find((r) => r.ovb === p && r.terc === "high");
    const blo = wbowl.find((r) => r.ovb === p && r.terc === "low");
    return {
      phase: `Ov ${p}`,
      low: lo?.runs_per_dismissal,
      high: hi?.runs_per_dismissal,
      econLow: blo?.run_rate,
      econHigh: bhi?.run_rate,
    };
  });

  const robData = phaseOrder.map((p) => ({
    phase: `Ov ${p}`,
    full: rob.full_index[p],
    noBuild: rob.without_buildup[p],
    levOnly: rob.leverage_only[p],
  }));

  const calib = (models.inn2.calibration as any[]).map((c) => ({
    pred: c.pred * 100,
    obs: c.obs * 100,
    n: c.n,
  }));

  return (
    <div className="space-y-7">
      <SectionTitle
        kicker="Validation"
        title="Does the index actually measure pressure?"
        blurb="A pressure definition is only meaningful if performance demonstrably degrades as it rises. Three tests: does output fall, does it survive controlling for the phase of the innings, and does it depend on any single pillar?"
      />

      {/* test 1 */}
      <Card>
        <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
          <div>
            <Pill tone="rr">Test 1</Pill>
            <div className="mt-2 text-[16px] font-extrabold">
              Batting output across pressure bands
            </div>
          </div>
          <div className="text-right text-[12px] text-muted">
            runs per dismissal{" "}
            <span className="font-bold text-rr-soft">
              −{fmt(press.rpd_drop_pct, 0)}%
            </span>{" "}
            · dismissal rate{" "}
            <span className="font-bold text-gold">+{fmt(press.wkt_rate_rise_pct, 0)}%</span>
          </div>
        </div>
        <ResponsiveContainer width="100%" height={300}>
          <ComposedChart data={bands} margin={{ top: 6, right: 12, bottom: 4, left: -8 }}>
            <CartesianGrid stroke={CHART_GRID} strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="band" {...axis} />
            <YAxis yAxisId="l" {...axis} />
            <YAxis yAxisId="r" orientation="right" {...axis} />
            <Tooltip contentStyle={tipStyle} />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            <Bar
              yAxisId="l"
              dataKey="runs_per_dismissal"
              name="Runs per dismissal"
              radius={[5, 5, 0, 0]}
            >
              {bands.map((_, i) => (
                <Cell key={i} fill={`rgba(230,23,127,${0.35 + i * 0.12})`} />
              ))}
            </Bar>
            <Line
              yAxisId="r"
              type="monotone"
              dataKey="wkt_per_100"
              name="Wickets per 100 balls"
              stroke="#f2c14e"
              strokeWidth={2.5}
              dot={{ r: 3.5 }}
            />
            <Line
              yAxisId="r"
              type="monotone"
              dataKey="run_rate"
              name="Run rate"
              stroke="#4ea8f2"
              strokeWidth={2}
              strokeDasharray="5 4"
              dot={{ r: 3 }}
            />
          </ComposedChart>
        </ResponsiveContainer>
        <p className="mt-3 text-[13px] leading-relaxed text-muted">
          The blue line is the point. Run rate is essentially flat — batters do not slow down under
          pressure, because high-pressure balls cluster where everyone is swinging anyway. What
          collapses is survival: runs per dismissal falls from{" "}
          {fmt(bands[0].runs_per_dismissal, 1)} to {fmt(bands[bands.length - 1].runs_per_dismissal, 1)}.
          Pressure charges a risk premium, and a strike-rate-based metric would never see it.
        </p>
      </Card>

      {/* test 2 */}
      <Card>
        <Pill tone="sky">Test 2</Pill>
        <div className="mt-2 text-[16px] font-extrabold">
          Controlling for the phase of the innings
        </div>
        <p className="mt-1.5 max-w-3xl text-[13px] leading-relaxed text-muted">
          The obvious objection: is this just measuring &ldquo;which over is it?&rdquo; So we split
          deliveries into top and bottom pressure terciles <em>within</em> each phase. The gap
          survives everywhere — and for bowlers it only behaved once build-up was made asymmetric.
        </p>
        <div className="mt-5 grid gap-5 lg:grid-cols-2">
          <div>
            <div className="mb-2 text-[12.5px] font-bold text-muted">
              Batting — runs per dismissal
            </div>
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={phaseData} margin={{ top: 4, right: 8, bottom: 4, left: -16 }}>
                <CartesianGrid stroke={CHART_GRID} strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="phase" {...axis} />
                <YAxis {...axis} />
                <Tooltip contentStyle={tipStyle} />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                <Bar dataKey="low" name="Low pressure" fill="#3c4187" radius={[4, 4, 0, 0]} />
                <Bar dataKey="high" name="High pressure" fill="#e6177f" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div>
            <div className="mb-2 text-[12.5px] font-bold text-muted">
              Bowling — runs conceded per over
            </div>
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={phaseData} margin={{ top: 4, right: 8, bottom: 4, left: -16 }}>
                <CartesianGrid stroke={CHART_GRID} strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="phase" {...axis} />
                <YAxis domain={[6, 12]} {...axis} />
                <Tooltip contentStyle={tipStyle} />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                <Bar dataKey="econLow" name="Low pressure" fill="#3c4187" radius={[4, 4, 0, 0]} />
                <Bar dataKey="econHigh" name="High pressure" fill="#4ea8f2" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </Card>

      {/* test 3 */}
      <Card>
        <Pill tone="gold">Test 3</Pill>
        <div className="mt-2 text-[16px] font-extrabold">
          Does the signal depend on one pillar?
        </div>
        <p className="mt-1.5 max-w-3xl text-[13px] leading-relaxed text-muted">
          Build-up is the pillar most at risk of flattering the result, since recent scoring
          autocorrelates with the current ball. Strip it out and the gap shrinks but survives. Strip
          everything except leverage and it almost vanishes outside the death overs — which is
          precisely why the index is a composite and not just a win-probability model.
        </p>
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={robData} margin={{ top: 14, right: 12, bottom: 4, left: -12 }}>
            <CartesianGrid stroke={CHART_GRID} strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="phase" {...axis} />
            <YAxis {...axis} unit="%" />
            <Tooltip contentStyle={tipStyle} />
            <Legend wrapperStyle={{ fontSize: 11 }} />
            <Bar dataKey="full" name="Full index" fill="#e6177f" radius={[4, 4, 0, 0]} />
            <Bar dataKey="noBuild" name="Without build-up" fill="#f2c14e" radius={[4, 4, 0, 0]} />
            <Bar dataKey="levOnly" name="Leverage only" fill="#4ea8f2" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
        <div className="mt-2 text-[11.5px] text-muted">
          Change in runs per dismissal, top vs bottom pressure tercile, within phase. More negative
          = the index is separating harder situations more sharply.
        </div>
      </Card>

      {/* reliability + calibration */}
      <div className="grid gap-3.5 lg:grid-cols-2">
        <Card>
          <Pill tone="mint">Repeatability</Pill>
          <div className="mt-2 text-[16px] font-extrabold">Which metrics are real skill?</div>
          <p className="mt-1.5 text-[12.5px] leading-relaxed text-muted">
            Matches dealt alternately by date into two halves. A metric that measures skill
            correlates across them; one that measures variance does not. Spearman–Brown converts the
            half-sample correlation to full-length reliability.
          </p>
          <div className="mt-4 overflow-x-auto">
            <table className="w-full text-[12.5px]">
              <thead>
                <tr className="border-b border-line text-left text-[11px] uppercase tracking-wider text-muted">
                  <th className="pb-2">Metric</th>
                  <th className="pb-2 text-right">Batting r</th>
                  <th className="pb-2 text-right">Bowling r</th>
                  <th className="pb-2 text-right">Verdict</th>
                </tr>
              </thead>
              <tbody className="tnum">
                {[
                  ["overall", "Overall impact/ball", "Real, durable skill"],
                  ["press", "Pressure impact/ball", "Weak but real"],
                  ["clutch", "Clutch premium", "Noise"],
                  ["pos_rate", "Match consistency", "Noise (bat) / weak (bowl)"],
                ].map(([k, label, verdict]) => {
                  const b = relBat[k]?.full_length_r ?? 0;
                  const l = relBowl[k]?.full_length_r ?? 0;
                  const strong = Math.max(b, l);
                  return (
                    <tr key={k} className="border-b border-line/40">
                      <td className="py-2 font-semibold">{label}</td>
                      <td className="py-2 text-right">{fmt(b, 2)}</td>
                      <td className="py-2 text-right">{fmt(l, 2)}</td>
                      <td className="py-2 text-right">
                        <span
                          className={
                            strong > 0.28
                              ? "text-mint"
                              : strong > 0.13
                              ? "text-gold"
                              : "text-rr-soft"
                          }
                        >
                          {verdict}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <p className="mt-3 text-[12.5px] leading-relaxed text-muted">
            This single table is why the model is built the way it is. If clutch were a durable
            trait we would rank on it directly. It isn&apos;t — so we rank on expected performance
            under pressure and let the clutch term act only as a tiebreaker.
          </p>
        </Card>

        <Card>
          <Pill tone="sky">Win probability</Pill>
          <div className="mt-2 text-[16px] font-extrabold">Chase model calibration</div>
          <p className="mt-1.5 text-[12.5px] leading-relaxed text-muted">
            Predicted win probability against what actually happened, in ten buckets across{" "}
            {models.inn2.n.toLocaleString()} chase deliveries. Points on the diagonal mean the model
            is honest — when it says 30%, teams win 30% of the time.
          </p>
          <ResponsiveContainer width="100%" height={270}>
            <ScatterChart margin={{ top: 14, right: 14, bottom: 6, left: -10 }}>
              <CartesianGrid stroke={CHART_GRID} strokeDasharray="3 3" />
              <XAxis
                type="number"
                dataKey="pred"
                name="Predicted"
                domain={[0, 100]}
                unit="%"
                {...axis}
              />
              <YAxis
                type="number"
                dataKey="obs"
                name="Observed"
                domain={[0, 100]}
                unit="%"
                {...axis}
              />
              <ZAxis type="number" dataKey="n" range={[50, 320]} />
              <Tooltip contentStyle={tipStyle} cursor={{ strokeDasharray: "3 3" }} />
              <Scatter data={calib} fill="#4ea8f2" />
              <Scatter
                data={[
                  { pred: 0, obs: 0 },
                  { pred: 100, obs: 100 },
                ]}
                line={{ stroke: "#9aa0cf", strokeDasharray: "5 5" }}
                shape={() => <g />}
              />
            </ScatterChart>
          </ResponsiveContainer>
          <div className="mt-1 grid grid-cols-3 gap-3 text-center">
            {[
              ["Brier", fmt(models.inn2.brier, 3), "0.25 = coin flip"],
              ["Log loss", fmt(models.inn2.log_loss, 3), "lower is better"],
              ["Matches", models.matches_fit, "used for fitting"],
            ].map(([l, v, s]) => (
              <div key={l as string}>
                <div className="text-[10.5px] uppercase tracking-wider text-muted">{l}</div>
                <div className="tnum text-[17px] font-extrabold text-text">{v}</div>
                <div className="text-[10.5px] text-muted">{s}</div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}
