"""OpenAI-compatible client helpers for on-prem Nemotron NIM.

The rest of InsightPulse can keep using OpenAI-style chat completions while
switching the endpoint by project.  The helper is intentionally conservative:
cloud keys are read only when a cloud provider is selected, and malformed LLM
JSON can fall back to the last good cached artifact.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Iterable, Optional, Type, TypeVar

from openai import OpenAI

try:  # Pydantic is optional for callers that only need dict JSON.
    from pydantic import BaseModel, ValidationError
except Exception:  # pragma: no cover - runtime dependency guard
    BaseModel = object  # type: ignore[misc,assignment]
    ValidationError = ValueError  # type: ignore[assignment]


T = TypeVar("T", bound=BaseModel)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY_PATH = ROOT / "data/projects/_registry.json"

PROVIDER_ON_PREM = "on-prem-nemotron"
PROVIDER_CLOUD_OPENAI = "cloud-openai"
PROVIDER_CLOUD_SUPER = "cloud-super"
PROVIDER_RULE_ONLY = "rule-based"

NIM_ENDPOINTS: dict[str, dict[str, Optional[str]]] = {
    PROVIDER_ON_PREM: {
        "base_url": os.getenv("NIM_LLM_BASE_URL", "http://localhost:8000/v1"),
        "api_key": os.getenv("NIM_LLM_API_KEY") or os.getenv("NVIDIA_API_KEY") or "nvapi-local-not-used",
        "model": os.getenv("NIM_LLM_MODEL", "nemotron-nano-9b"),
    },
    PROVIDER_CLOUD_OPENAI: {
        "base_url": os.getenv("OPENAI_BASE_URL") or None,
        "api_key": os.getenv("OPENAI_API_KEY"),
        "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    },
    PROVIDER_CLOUD_SUPER: {
        "base_url": os.getenv("NIM_SUPER_BASE_URL", "http://localhost:8010/v1"),
        "api_key": os.getenv("NIM_SUPER_API_KEY", "nvapi-local-not-used"),
        "model": os.getenv("NIM_SUPER_MODEL", "nemotron-3-super-120b-a12b"),
    },
}


def normalize_provider(provider: Optional[str]) -> str:
    """Map UI/config aliases to known provider IDs."""
    value = (provider or PROVIDER_ON_PREM).strip().lower()
    aliases = {
        "nemotron": PROVIDER_ON_PREM,
        "on_prem_nemotron": PROVIDER_ON_PREM,
        "on-prem": PROVIDER_ON_PREM,
        "local": PROVIDER_ON_PREM,
        "openai": PROVIDER_CLOUD_OPENAI,
        "cloud": PROVIDER_CLOUD_OPENAI,
        "cloud_api": PROVIDER_CLOUD_OPENAI,
        "cloud-openai": PROVIDER_CLOUD_OPENAI,
        "super": PROVIDER_CLOUD_SUPER,
        "cloud-super": PROVIDER_CLOUD_SUPER,
        "rule": PROVIDER_RULE_ONLY,
        "rule-based": PROVIDER_RULE_ONLY,
        "no-llm": PROVIDER_RULE_ONLY,
    }
    return aliases.get(value, value)


def load_registry(registry_path: Optional[str | Path] = None) -> dict[str, Any]:
    """Load the project registry, returning an empty registry on errors."""
    path = Path(registry_path or os.getenv("REGISTRY_PATH") or DEFAULT_REGISTRY_PATH)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"projects": {}}


def get_project_config(
    project_id: str = "PRN_N9",
    registry_path: Optional[str | Path] = None,
) -> dict[str, Any]:
    """Return registry metadata for both supported registry shapes."""
    projects = load_registry(registry_path).get("projects", {})
    if isinstance(projects, dict):
        return dict(projects.get(project_id, {}))
    if isinstance(projects, list):
        for project in projects:
            if project.get("project_id") == project_id:
                return dict(project)
    return {}


def get_provider_for_project(
    project_id: str = "PRN_N9",
    registry_path: Optional[str | Path] = None,
    explicit_provider: Optional[str] = None,
) -> str:
    """Resolve the LLM provider for a project."""
    if explicit_provider:
        return normalize_provider(explicit_provider)
    project = get_project_config(project_id, registry_path)
    return normalize_provider(project.get("processing") or os.getenv("INSIGHTPULSE_LLM_PROVIDER"))


def project_multimodal_enabled(
    project_id: str = "PRN_N9",
    registry_path: Optional[str | Path] = None,
    explicit: Optional[bool] = None,
) -> bool:
    """Resolve whether a project should run multimodal preprocessing."""
    if explicit is not None:
        return bool(explicit)
    project = get_project_config(project_id, registry_path)
    return bool(project.get("multimodal") or os.getenv("INSIGHTPULSE_MULTIMODAL", "").lower() in {"1", "true", "yes"})


def get_llm_client(provider: str = PROVIDER_ON_PREM) -> tuple[OpenAI, str, str]:
    """Return ``(OpenAI client, model name, normalized provider)``."""
    normalized = normalize_provider(provider)
    if normalized == PROVIDER_RULE_ONLY:
        raise ValueError("rule-based provider does not create an LLM client")
    if normalized not in NIM_ENDPOINTS:
        raise ValueError(f"Unsupported LLM provider: {provider}")

    cfg = NIM_ENDPOINTS[normalized]
    api_key = cfg.get("api_key")
    if not api_key:
        raise RuntimeError(f"Missing API key for provider: {normalized}")
    client = OpenAI(base_url=cfg.get("base_url"), api_key=api_key)
    return client, str(cfg["model"]), normalized


def provider_failover_order(provider: str) -> list[str]:
    """Provider order with sovereignty-first defaults."""
    primary = normalize_provider(provider)
    if primary == PROVIDER_RULE_ONLY:
        return [PROVIDER_RULE_ONLY]
    if primary == PROVIDER_CLOUD_OPENAI:
        return [PROVIDER_CLOUD_OPENAI, PROVIDER_ON_PREM, PROVIDER_RULE_ONLY]
    if primary == PROVIDER_CLOUD_SUPER:
        return [PROVIDER_CLOUD_SUPER, PROVIDER_ON_PREM, PROVIDER_CLOUD_OPENAI, PROVIDER_RULE_ONLY]
    return [PROVIDER_ON_PREM, PROVIDER_CLOUD_OPENAI, PROVIDER_RULE_ONLY]


def extract_json_object(text: str) -> dict[str, Any]:
    """Parse a JSON object, tolerating accidental prose around it."""
    try:
        parsed = json.loads(text or "{}")
    except json.JSONDecodeError:
        start = (text or "").find("{")
        end = (text or "").rfind("}")
        if start < 0 or end <= start:
            raise
        parsed = json.loads(text[start : end + 1])
    if not isinstance(parsed, dict):
        raise ValueError("LLM response must be a JSON object")
    return parsed


def _validate_required_keys(data: dict[str, Any], required_keys: Iterable[str]) -> None:
    missing = [key for key in required_keys if key not in data]
    if missing:
        raise ValueError(f"Missing required JSON keys: {', '.join(missing)}")


def generate_json(
    *,
    client: OpenAI,
    model: str,
    prompt: str,
    system: str,
    provider: str,
    required_keys: Iterable[str] = (),
    cache_path: Optional[str | Path] = None,
    max_retries: int = 2,
    temperature: float = 0.3,
    max_tokens: Optional[int] = None,
) -> dict[str, Any]:
    """Generate and validate a JSON object via an OpenAI-compatible endpoint."""
    messages: list[dict[str, str]] = [
        {"role": "system", "content": system},
        {"role": "user", "content": prompt},
    ]
    last_err: Optional[str] = None

    for _ in range(max_retries + 1):
        try:
            kwargs: dict[str, Any] = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "response_format": {"type": "json_object"},
            }
            if max_tokens:
                kwargs["max_tokens"] = max_tokens
            resp = client.chat.completions.create(**kwargs)
            content = resp.choices[0].message.content or "{}"
            parsed = extract_json_object(content)
            _validate_required_keys(parsed, required_keys)
            parsed["llm_provider"] = provider
            parsed["llm_model"] = model
            if cache_path:
                Path(cache_path).parent.mkdir(parents=True, exist_ok=True)
                Path(cache_path).write_text(json.dumps(parsed, ensure_ascii=False, indent=2), encoding="utf-8")
            return parsed
        except Exception as exc:
            last_err = str(exc)
            messages.append({"role": "assistant", "content": locals().get("content", "")})
            messages.append({
                "role": "user",
                "content": (
                    "The previous response was invalid. "
                    f"Error: {last_err}. Return ONLY valid JSON matching the requested schema."
                ),
            })
            time.sleep(1)

    if cache_path and Path(cache_path).exists():
        cached = json.loads(Path(cache_path).read_text(encoding="utf-8"))
        if isinstance(cached, dict):
            cached.setdefault("llm_provider", f"{provider}_cached")
            cached.setdefault("llm_model", model)
            return cached

    raise RuntimeError(f"LLM JSON generation failed after retries: {last_err}")


def generate_model(
    *,
    client: OpenAI,
    model: str,
    prompt: str,
    schema: Type[T],
    provider: str,
    system: str,
    cache_path: Optional[str | Path] = None,
    max_retries: int = 2,
    temperature: float = 0.3,
) -> T:
    """Generate a Pydantic-validated response for stricter future callers."""
    data = generate_json(
        client=client,
        model=model,
        prompt=prompt,
        system=system,
        provider=provider,
        cache_path=cache_path,
        max_retries=max_retries,
        temperature=temperature,
    )
    try:
        return schema.model_validate(data)  # type: ignore[attr-defined]
    except ValidationError:
        if cache_path and Path(cache_path).exists():
            cached = json.loads(Path(cache_path).read_text(encoding="utf-8"))
            return schema.model_validate(cached)  # type: ignore[attr-defined]
        raise
