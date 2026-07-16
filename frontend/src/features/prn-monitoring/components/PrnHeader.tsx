import { Upload, Moon, Sun } from "lucide-react";
import type { StateFilter } from "../types/prn";
import type { ThemeMode } from "../hooks/useTheme";

interface Props {
  lastUpdated: string;
  state: StateFilter;
  onStateChange: (s: StateFilter) => void;
  dataMode: string;
  onUpload?: (file: File) => void;
  theme?: ThemeMode;
  onToggleTheme?: () => void;
}

export function PrnHeader({ lastUpdated, state, onStateChange, dataMode, onUpload, theme, onToggleTheme }: Props) {
  return (
    <header className="border-b border-surface-border bg-surface-raised/80 px-4 py-4 backdrop-blur sm:px-6">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="text-lg font-semibold tracking-tight text-slate-100 sm:text-xl">
            PRN Johor & Negeri Sembilan Monitoring
          </h1>
          <p className="mt-1 max-w-2xl text-sm text-slate-400">
            Realtime election intelligence, source coverage, DUN-level query readiness
          </p>
          <p className="mt-2 text-xs text-slate-500">
            Last updated: <span className="tabular-nums text-slate-400">{lastUpdated}</span>
            <span className="mx-2">·</span>
            Data: <span className="uppercase text-slate-400">{dataMode}</span>
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {(["Both", "Johor", "Negeri Sembilan"] as StateFilter[]).map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => onStateChange(s)}
              className={`rounded border px-3 py-1.5 text-xs font-medium transition ${
                state === s
                  ? "border-sky-600 bg-sky-950/50 text-sky-200"
                  : "border-surface-border bg-surface text-slate-400 hover:border-slate-500"
              }`}
            >
              {s}
            </button>
          ))}
          {onToggleTheme && (
            <button
              type="button"
              onClick={onToggleTheme}
              className="flex items-center gap-1.5 rounded border border-surface-border bg-surface px-3 py-1.5 text-xs text-slate-400 hover:border-slate-500"
              title={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
            >
              {theme === "dark" ? <Sun className="h-3.5 w-3.5" /> : <Moon className="h-3.5 w-3.5" />}
              {theme === "dark" ? "Light" : "Dark"}
            </button>
          )}
          {onUpload && (
            <label className="flex cursor-pointer items-center gap-1.5 rounded border border-surface-border bg-surface px-3 py-1.5 text-xs text-slate-400 hover:border-slate-500">
              <Upload className="h-3.5 w-3.5" />
              Upload Excel
              <input
                type="file"
                accept=".xlsx,.xls"
                className="hidden"
                onChange={(e) => {
                  const f = e.target.files?.[0];
                  if (f) onUpload(f);
                }}
              />
            </label>
          )}
        </div>
      </div>
    </header>
  );
}
