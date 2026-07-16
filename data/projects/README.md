# InsightPulse — Project Data Storage

## Structure

```
data/projects/
├── _registry.json              # All projects (IDs, categories, clients)
├── political/
│   ├── PRN/                    # PRN negeri — PRN_N9, PRN_Johor, PRN_Melaka
│   ├── pas_break_2026/         # PAS–Bersatu narrative (cross-state socmed)
│   ├── pas_bersatu_baseline/   # JITP baseline Mei 2026
│   └── prn_johor_2026/         # legacy → data in PRN/PRN_Johor
├── sme/
│   └── smebank/
└── agency/
    └── kdebwm/
```

Each project folder:

```
{project_id}/
├── metadata.json    # Crawl history, keywords, latest master
├── crawls/          # One CSV per crawl session
├── master/          # Merged / final datasets for dashboard
└── reports/         # EXCO briefs, exports
```

## Workflow

1. **UI crawl** → auto saves to `data/combined/` (staging)
2. **If project selected** → copy also to `data/projects/{category}/{id}/crawls/`
3. **Dashboard** → read from `master/` only
4. **combined/** → staging; safe to clean after 14 days

## Project IDs (for Crawl UI dropdown)

**Tambah projek baru — terus dari app:** klik **+ Projek Baru** (tanpa edit JSON).

Dropdown auto-load dari `/api/projects`.

| ID | Use for |
|---|---|
| `pas_break_2026` | PAS–Bersatu · PRN 3 negeri |
| `pas_bersatu_baseline` | Historical JITP data |
| `prn_johor_2026` | PRN Johor dashboard |
| `smebank` | SME Bank EWS |
| `kdebwm` | KDEBWM complaints |

## Crawl 2 (News)

Select project: **pas_break_2026** in UI → file goes to  
`data/projects/political/pas_break_2026/crawls/`
