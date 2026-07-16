#!/usr/bin/env python3
"""Smoke test NVIDIA hosted Nemotron/NIM OpenAI-compatible endpoint.

Do not paste secrets into chat. Put the key in .env or .env.nemotron:

  NVIDIA_API_KEY=nvapi-...
  NIM_LLM_BASE_URL=https://integrate.api.nvidia.com/v1
  NIM_LLM_MODEL=nvidia/llama-3.3-nemotron-super-49b-v1.5

Then run:

  NEImpulse/bin/python scripts/test_nemotron_hosted.py
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from openai import OpenAI  # noqa: E402


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def main() -> int:
    load_env_file(ROOT / ".env")
    load_env_file(ROOT / ".env.nemotron")

    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default=os.getenv("NIM_LLM_BASE_URL", "https://integrate.api.nvidia.com/v1"))
    parser.add_argument("--model", default=os.getenv("NIM_LLM_MODEL", "nvidia/llama-3.3-nemotron-super-49b-v1.5"))
    parser.add_argument("--api-key", default=os.getenv("NIM_LLM_API_KEY") or os.getenv("NVIDIA_API_KEY"))
    parser.add_argument("--list-models", action="store_true", help="List available model IDs for this API key")
    args = parser.parse_args()

    if not args.api_key or args.api_key.startswith("nvapi-xxxxxxxx"):
        print("❌ Missing NVIDIA API key. Set NVIDIA_API_KEY=nvapi-... in .env or .env.nemotron")
        return 2

    client = OpenAI(base_url=args.base_url, api_key=args.api_key)

    print(f"Base URL: {args.base_url}")
    print(f"Model: {args.model}")

    if args.list_models:
        models = client.models.list()
        print("Available models containing 'nemotron':")
        for model in models.data:
            mid = getattr(model, "id", "")
            if "nemotron" in mid.lower():
                print(f"  - {mid}")
        return 0

    response = client.chat.completions.create(
        model=args.model,
        messages=[
            {
                "role": "system",
                "content": "You are a concise Malaysian political intelligence assistant. Reply in Bahasa Melayu.",
            },
            {
                "role": "user",
                "content": "Ujian ringkas: beri 3 fokus analisis PRN Negeri Sembilan dalam JSON ringkas.",
            },
        ],
        temperature=0.2,
        max_tokens=512,
    )
    print("\n✅ Nemotron hosted endpoint OK\n")
    print(response.choices[0].message.content)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
