"use client";
import React from "react";

export function Card({
  children,
  className = "",
  pad = true,
}: {
  children: React.ReactNode;
  className?: string;
  pad?: boolean;
}) {
  return (
    <div className={`panel ${pad ? "p-5" : ""} ${className}`}>{children}</div>
  );
}

export function SectionTitle({
  kicker,
  title,
  blurb,
}: {
  kicker: string;
  title: string;
  blurb?: string;
}) {
  return (
    <div className="mb-6">
      <div className="text-[11px] font-bold uppercase tracking-[0.22em] text-rr">
        {kicker}
      </div>
      <h2 className="mt-1.5 text-2xl font-extrabold tracking-tight text-text md:text-[28px]">
        {title}
      </h2>
      {blurb && (
        <p className="mt-2 max-w-3xl text-[14px] leading-relaxed text-muted">
          {blurb}
        </p>
      )}
    </div>
  );
}

export function Stat({
  label,
  value,
  sub,
  tone = "default",
}: {
  label: string;
  value: React.ReactNode;
  sub?: string;
  tone?: "default" | "rr" | "gold" | "mint";
}) {
  const tones: Record<string, string> = {
    default: "text-text",
    rr: "text-rr-soft",
    gold: "text-gold",
    mint: "text-mint",
  };
  return (
    <Card className="min-w-0">
      <div className="text-[10.5px] font-semibold uppercase tracking-[0.16em] text-muted">
        {label}
      </div>
      <div className={`tnum mt-1.5 text-[26px] font-extrabold leading-none ${tones[tone]}`}>
        {value}
      </div>
      {sub && <div className="mt-1.5 text-[12px] leading-snug text-muted">{sub}</div>}
    </Card>
  );
}

export function Pill({
  children,
  tone = "line",
}: {
  children: React.ReactNode;
  tone?: "line" | "rr" | "gold" | "mint" | "sky";
}) {
  const tones: Record<string, string> = {
    line: "border-line text-muted",
    rr: "border-rr/50 text-rr-soft bg-rr/10",
    gold: "border-gold/40 text-gold bg-gold/10",
    mint: "border-mint/40 text-mint bg-mint/10",
    sky: "border-sky/40 text-sky bg-sky/10",
  };
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-[3px] text-[11px] font-semibold ${tones[tone]}`}
    >
      {children}
    </span>
  );
}

/** Horizontal bar used for z-scores and impact comparisons. */
export function Bar({
  value,
  max,
  tone = "rr",
}: {
  value: number;
  max: number;
  tone?: "rr" | "mint" | "sky" | "gold";
}) {
  const colors: Record<string, string> = {
    rr: "bg-rr",
    mint: "bg-mint",
    sky: "bg-sky",
    gold: "bg-gold",
  };
  const pct = Math.max(0, Math.min(100, (Math.abs(value) / max) * 100));
  const neg = value < 0;
  return (
    <div className="relative h-[7px] w-full overflow-hidden rounded-full bg-line/50">
      <div
        className={`absolute top-0 h-full rounded-full ${neg ? "bg-gold/70" : colors[tone]}`}
        style={{ left: neg ? `${50 - pct / 2}%` : "50%", width: `${pct / 2}%` }}
      />
      <div className="absolute left-1/2 top-0 h-full w-px bg-muted/40" />
    </div>
  );
}

export function fmt(n: number | null | undefined, d = 2) {
  if (n === null || n === undefined || Number.isNaN(n)) return "—";
  return n.toFixed(d);
}

export function signed(n: number | null | undefined, d = 3) {
  if (n === null || n === undefined || Number.isNaN(n)) return "—";
  return `${n >= 0 ? "+" : ""}${n.toFixed(d)}`;
}

export const CHART_GRID = "#262a63";
export const CHART_AXIS = "#9aa0cf";
