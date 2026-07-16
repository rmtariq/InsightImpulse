import {
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
  type ColumnDef,
  type SortingState,
} from "@tanstack/react-table";
import { ExternalLink } from "lucide-react";
import { useMemo, useState } from "react";
import { formatDate } from "../lib/prnFormatters";
import { EnabledBadge, StatusBadge } from "./StatusBadge";
import { PriorityBadge } from "./PriorityBadge";
import type { UrlSourceRow } from "../types/prn";

const columns: ColumnDef<UrlSourceRow>[] = [
  { accessorKey: "state", header: "State", size: 80 },
  { accessorKey: "platform", header: "Platform", size: 90 },
  { accessorKey: "category", header: "Category", size: 100 },
  { accessorKey: "name", header: "Name", size: 140 },
  {
    accessorKey: "url",
    header: "URL",
    cell: ({ row }) => (
      <a
        href={row.original.url}
        target="_blank"
        rel="noopener noreferrer"
        className="inline-flex max-w-[200px] items-center gap-1 truncate text-sky-400 hover:text-sky-300"
        onClick={(e) => e.stopPropagation()}
      >
        <span className="truncate">{row.original.url}</span>
        <ExternalLink className="h-3 w-3 shrink-0" />
      </a>
    ),
  },
  {
    accessorKey: "priority",
    header: "Priority",
    cell: ({ row }) => <PriorityBadge level={String(row.original.priority)} />,
  },
  { accessorKey: "crawlFrequency", header: "Frequency" },
  {
    accessorKey: "enabled",
    header: "Enabled",
    cell: ({ row }) => <EnabledBadge enabled={row.original.enabled} />,
  },
  {
    accessorKey: "verificationStatus",
    header: "Verification",
    cell: ({ row }) => <StatusBadge status={row.original.verificationStatus} />,
  },
  { accessorKey: "tosRisk", header: "ToS" },
  { accessorKey: "electionRelevance", header: "Relevance" },
  {
    accessorKey: "lastVerified",
    header: "Verified",
    cell: ({ row }) => formatDate(row.original.lastVerified),
  },
];

export function PrnSourceTable({ data }: { data: UrlSourceRow[] }) {
  const [sorting, setSorting] = useState<SortingState>([{ id: "priority", desc: true }]);
  const cols = useMemo(() => columns, []);

  const table = useReactTable({
    data,
    columns: cols,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    initialState: { pagination: { pageSize: 15 } },
  });

  return (
    <div className="rounded border border-surface-border bg-surface-raised">
      <div className="max-h-[480px] overflow-auto">
        <table className="w-full min-w-[960px] text-left text-xs">
          <thead className="sticky top-0 z-10 bg-slate-900">
            {table.getHeaderGroups().map((hg) => (
              <tr key={hg.id} className="border-b border-surface-border">
                {hg.headers.map((h) => (
                  <th
                    key={h.id}
                    className="cursor-pointer whitespace-nowrap px-2 py-2 font-medium text-slate-400"
                    onClick={h.column.getToggleSortingHandler()}
                  >
                    {flexRender(h.column.columnDef.header, h.getContext())}
                    {{ asc: " ↑", desc: " ↓" }[h.column.getIsSorted() as string] ?? null}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            {table.getRowModel().rows.map((row) => (
              <tr
                key={row.id}
                className="border-b border-surface-border/50 hover:bg-slate-800/50 cursor-pointer"
                onClick={() => window.open(row.original.url, "_blank")}
              >
                {row.getVisibleCells().map((cell) => (
                  <td key={cell.id} className="px-2 py-1.5 text-slate-300">
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="flex items-center justify-between border-t border-surface-border px-3 py-2 text-xs text-slate-500">
        <span>{data.length} sources</span>
        <div className="flex gap-2">
          <button type="button" disabled={!table.getCanPreviousPage()} onClick={() => table.previousPage()} className="rounded border border-surface-border px-2 py-0.5 disabled:opacity-40">Prev</button>
          <span className="tabular-nums">Page {table.getState().pagination.pageIndex + 1}</span>
          <button type="button" disabled={!table.getCanNextPage()} onClick={() => table.nextPage()} className="rounded border border-surface-border px-2 py-0.5 disabled:opacity-40">Next</button>
        </div>
      </div>
    </div>
  );
}
