# InsightPulse × Nemotron Ops

This integration keeps the existing InsightPulse pipeline intact and adds
Nemotron NIM behind OpenAI-compatible endpoints.

## What Changes

- `scripts/analyze_naratif_agentic.py` now reads the project LLM provider and tries:
  `on-prem-nemotron → cloud-openai → rule-based`.
- `scripts/regenerate_naratif_docx_gpt4o.py` uses the same provider routing for
  DOCX action-plan generation.
- `scripts/multimodal_router.py` converts media rows into text before Malay BERT.
- `backend/nim_safety.py` can enrich alert/action scoring when `NIM_SAFETY_ENABLED=true`.
- PRN/Narrative projects in `data/projects/_registry.json` default to:
  `processing: on-prem-nemotron`, `multimodal: true`.

## Ports

| Service | Host Port |
|---|---:|
| Nemotron LLM | 8000 |
| InsightPulse FastAPI | 8001 |
| Nemotron Omni | 8002 |
| Nemotron Safety | 8003 |
| Nemotron OCR | 8004 |
| Nemotron ASR HTTP | 9000 |
| Nemotron ASR gRPC | 50051 |
| War Room LIVE | 8080 |
| Streamlit Naratif | 8501 |

## Start NIM

```bash
cp .env.nemotron.example .env.nemotron
# Edit .env.nemotron and set NGC_API_KEY.

sudo mkdir -p /opt/nim/cache
sudo chmod -R a+w /opt/nim/cache

docker compose --env-file .env.nemotron -f docker-compose.nemotron.yml up -d nim-llm
curl -s http://localhost:8000/v1/health/ready
```

Optional multimodal stack:

```bash
docker compose --env-file .env.nemotron -f docker-compose.nemotron.yml --profile multimodal up -d
```

Optional safety stack:

```bash
docker compose --env-file .env.nemotron -f docker-compose.nemotron.yml --profile safety up -d
export NIM_SAFETY_ENABLED=true
```

## Run Agentic Narrative With Nemotron

```bash
NEImpulse/bin/python scripts/analyze_naratif_agentic.py --rebuild --project-id PRN_N9
```

Force a provider:

```bash
NEImpulse/bin/python scripts/analyze_naratif_agentic.py --project-id PRN_N9 --llm-provider cloud-openai
NEImpulse/bin/python scripts/analyze_naratif_agentic.py --project-id PRN_N9 --llm-provider rule-based
```

## Route Multimodal Crawl Output

JSON:

```bash
NEImpulse/bin/python scripts/multimodal_router.py \
  --input data/smart_crawlers/tiktok/items.json \
  --output data/smart_crawlers/tiktok/items_routed.json \
  --project-id PRN_N9 \
  --merge-text
```

CSV:

```bash
NEImpulse/bin/python scripts/multimodal_router.py \
  --input data/smart_crawlers/tiktok/tiktok_prn.csv \
  --output data/smart_crawlers/tiktok/tiktok_prn_routed.csv \
  --project-id PRN_N9 \
  --merge-text
```

## Acceptance Checks

- `curl http://localhost:8000/v1/health/ready` returns ready.
- `analyze_naratif_agentic.py` writes `naratif_agentic_brief.json` with
  `llm_provider: on-prem-nemotron`.
- No traffic to `api.openai.com`/`api.anthropic.com` when using on-prem and NIM is healthy.
- `multimodal_router.py --limit 5 --merge-text` adds `derived_text` to media rows.
- With `NIM_SAFETY_ENABLED=true`, high-risk rows get `nim_safety_*` columns and critical alerts.
