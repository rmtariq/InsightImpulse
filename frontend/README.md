# InsightPulse PRN Monitoring Dashboard

Production-grade React dashboard for **PRN Johor & Negeri Sembilan** election intelligence.

## Stack

- React 19 + TypeScript
- Vite 6
- Tailwind CSS 3
- TanStack Table 8
- Recharts 2
- lucide-react
- xlsx (workbook upload)

## Quick start (unified — port 8080)

From repo root:

```bash
bash scripts/start_prn_warroom_prototype.sh
```

Open:
- **War Room:** http://localhost:8080/
- **PRN Intel (React):** http://localhost:8080/insightpulse/prn-monitoring/

Rebuild React only:

```bash
bash scripts/build_prn_react_dashboard.sh
```

## Dev mode (Vite hot reload — port 5173)

```bash
cd frontend
npm install
npm run sync-prn-data
npm run dev
```

Open: http://localhost:5173/insightpulse/prn-monitoring/

## Data modes

1. **Manifest (default)** — loads `/data/prn_excel_intel_manifest.json`
2. **Workbook upload** — use header "Upload Excel" with `Terkini_20062026_PRN_N9_Johor_Melaka_Update_2026.xlsx`
3. **Mock fallback** — if manifest missing

Refresh manifest from repo:

```bash
python3 scripts/import_prn_excel_intel.py
npm run sync-prn-data
```

## Build

```bash
npm run build
npm run preview
```

## Route

`/insightpulse/prn-monitoring`

## Feature module

`src/features/prn-monitoring/`

Melaka data is parsed but filtered out of the main Johor + N9 view.
