import {
  flexRender,
  getCoreRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
  type ColumnDef,
  type SortingState,
} from "@tanstack/react-table";
import { useMemo, useState } from "react";
import { formatDate } from "../lib/prnFormatters";
import { PriorityBadge } from "./PriorityBadge";
import { StatusBadge } from "./StatusBadge";
import type { DunKeywordRow } from "../types/prn";

interface Props {
  data: DunKeywordRow[];
  onSelect: (row: DunKeywordRow) => void;
}

export function PrnDunTable({ data, onSelect }: Props) {
  const [sorting, setSorting] = useState<SortingState>([{ id: "monitoringPriorityScore", desc: true }]);

  const columns = useMemo<ColumnDef<DunKeywordRow>[]>(
    () => [
      { accessorKey: "state", header: "State" },
      { accessorKey: "dunCode", header: "Code" },
      { accessorKey: "dunName", header: "DUN" },
      { accessorKey: "parlimenName", header: "Parlimen" },
      { accessorKey: "district", header: "District" },
      { accessorKey: "areaType", header: "Area" },
      {
        accessorKey: "monitoringPriorityScore",
        header: "Score",
        cell: ({ row }) => <span className="tabular-nums font-medium">{row.original.monitoringPriorityScore}</span>,
      },
      {
        accessorKey: "monitoringPriority",
        header: "Priority",
        cell: ({ row }) => <PriorityBadge level={row.original.monitoringPriority} />,
      },
      {
        accessorKey: "electionStatus2026",
        header: "Status",
        cell: ({ row }) => <StatusBadge status={row.original.electionStatus2026} />,
      },
      { accessorKey: "nominationDate", header: "Nomination", cell: ({ row }) => formatDate(row.original.nominationDate) },
      { accessorKey: "earlyVotingDate", header: "Early vote", cell: ({ row }) => formatDate(row.original.earlyVotingDate) },
      { accessorKey: "pollingDate", header: "Polling", cell: ({ row }) => formatDate(row.original.pollingDate) },
      { accessorKey: "operationalPhase", header: "Phase" },
    ],
    [],
  );

  const table = useReactTable({
    data,
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    initialState: { pagination: { pageSize: 20 } },
  });

  return (
    <div className="rounded border border-surface-border bg-surface-raised">
      <div className="max-h-[520px] overflow-auto">
        <table className="w-full min-w-[1100px] text-left text-xs">
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
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            {table.getRowModel().rows.map((row) => (
              <tr
                key={row.id}
                className="cursor-pointer border-b border-surface-border/50 hover:bg-slate-800/50"
                onClick={() => onSelect(row.original)}
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
        <span>{data.length} DUN seats</span>
        <div className="flex gap-2">
          <button type="button" disabled={!table.getCanPreviousPage()} onClick={() => table.previousPage()} className="rounded border border-surface-border px-2 py-0.5 disabled:opacity-40">Prev</button>
          <button type="button" disabled={!table.getCanNextPage()} onClick={() => table.nextPage()} className="rounded border border-surface-border px-2 py-0.5 disabled:opacity-40">Next</button>
        </div>
      </div>
    </div>
  );
}
