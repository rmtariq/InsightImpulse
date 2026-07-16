import clsx from "clsx";
import type { PriorityLevel } from "../types/prn";

const styles: Record<PriorityLevel, string> = {
  CRITICAL: "bg-red-950/60 text-red-300 border-red-800",
  HIGH: "bg-orange-950/60 text-orange-300 border-orange-800",
  MEDIUM: "bg-amber-950/60 text-amber-300 border-amber-800",
  LOW: "bg-zinc-800/80 text-zinc-300 border-zinc-600",
};

export function PriorityBadge({ level }: { level: string }) {
  const key = (level?.toUpperCase() || "LOW") as PriorityLevel;
  const cls = styles[key] ?? styles.LOW;
  return (
    <span className={clsx("inline-flex rounded border px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide", cls)}>
      {key}
    </span>
  );
}
