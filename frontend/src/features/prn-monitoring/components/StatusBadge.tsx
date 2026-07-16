import clsx from "clsx";

function statusClass(status: string): string {
  const s = status.toUpperCase();
  if (s.includes("DISSOLVED")) return "bg-rose-950/60 text-rose-300 border-rose-800";
  if (s.includes("VERIFIED") && s.includes("OFFICIAL")) return "bg-emerald-950/60 text-emerald-300 border-emerald-800";
  if (s.includes("DOMAIN_ONLY")) return "bg-amber-950/60 text-amber-300 border-amber-800";
  if (s.includes("MANUAL") || s.includes("PENDING")) return "bg-red-950/50 text-red-200 border-red-800";
  if (s.includes("NOT_DISSOLVED") || s.includes("NOTDISSOLVED")) return "bg-slate-800 text-slate-300 border-slate-600";
  return "bg-slate-800/80 text-slate-300 border-slate-600";
}

export function StatusBadge({ status }: { status: string }) {
  const label = status.replace(/_/g, " ");
  return (
    <span className={clsx("inline-flex rounded border px-1.5 py-0.5 text-[10px] font-medium", statusClass(status))}>
      {label}
    </span>
  );
}

export function EnabledBadge({ enabled }: { enabled: boolean }) {
  return (
    <span
      className={clsx(
        "inline-flex rounded border px-1.5 py-0.5 text-[10px] font-medium",
        enabled ? "border-emerald-800 bg-emerald-950/50 text-emerald-300" : "border-zinc-600 bg-zinc-800 text-zinc-400",
      )}
    >
      {enabled ? "Enabled" : "Disabled"}
    </span>
  );
}
