"""
Project-based data storage for InsightPulse multi-client crawls.

Engine output (smart_crawlers → analyzed → combined) stays unchanged.
When project_id is set, combined CSV is also promoted to data/projects/.
"""

from __future__ import annotations

import json
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECTS_ROOT = Path("data/projects")
REGISTRY_FILE = PROJECTS_ROOT / "_registry.json"


def _slug(text: str, max_len: int = 40) -> str:
    s = re.sub(r"[^\w\s-]", "", text.lower())
    s = re.sub(r"[\s_-]+", "_", s).strip("_")
    return s[:max_len] or "crawl"


def load_registry() -> Dict[str, Any]:
    if REGISTRY_FILE.exists():
        with open(REGISTRY_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {"projects": {}, "categories": ["political", "sme", "agency", "commercial"]}


def save_registry(registry: Dict[str, Any]) -> None:
    REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(REGISTRY_FILE, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)


def get_project(project_id: str) -> Optional[Dict[str, Any]]:
    return load_registry().get("projects", {}).get(project_id)


def project_dir(project_id: str) -> Path:
    meta = get_project(project_id)
    if not meta:
        raise ValueError(f"Unknown project_id: {project_id}")
    return PROJECTS_ROOT / meta["category"] / project_id


def ensure_project_dirs(project_id: str) -> Dict[str, Path]:
    base = project_dir(project_id)
    dirs = {
        "root": base,
        "master": base / "master",
        "crawls": base / "crawls",
        "reports": base / "reports",
    }
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)
    return dirs


def metadata_path(project_id: str) -> Path:
    return project_dir(project_id) / "metadata.json"


def load_metadata(project_id: str) -> Dict[str, Any]:
    path = metadata_path(project_id)
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    meta = get_project(project_id) or {}
    return {
        "project_id": project_id,
        "name": meta.get("name", project_id),
        "category": meta.get("category", "political"),
        "client": meta.get("client", ""),
        "keywords": meta.get("default_keywords", []),
        "crawls": [],
        "masters": [],
        "updated_at": None,
    }


def save_metadata(project_id: str, metadata: Dict[str, Any]) -> None:
    ensure_project_dirs(project_id)
    metadata["updated_at"] = datetime.now().isoformat()
    with open(metadata_path(project_id), "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)


def promote_combined_to_project(
    project_id: str,
    combined_filepath: Path,
    *,
    crawl_label: str = "crawl",
    platforms: Optional[List[str]] = None,
    query: str = "",
    date_range: str = "",
    row_count: int = 0,
    copy_to_master: bool = False,
) -> Path:
    """Copy combined CSV into project crawls/ and update metadata."""
    dirs = ensure_project_dirs(project_id)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    label = _slug(crawl_label or "crawl")
    dest_name = f"{label}_{ts}.csv"
    dest = dirs["crawls"] / dest_name
    shutil.copy2(combined_filepath, dest)

    meta = load_metadata(project_id)
    entry = {
        "id": f"{label}_{ts}",
        "file": f"crawls/{dest_name}",
        "source_combined": str(combined_filepath),
        "platforms": platforms or [],
        "query": query[:200],
        "date_range": date_range,
        "rows": row_count,
        "saved_at": datetime.now().isoformat(),
    }
    meta.setdefault("crawls", []).append(entry)

    if copy_to_master:
        master_name = f"{_slug(get_project(project_id).get('master_prefix', project_id))}_Master_{ts}.csv"
        master_path = dirs["master"] / master_name
        shutil.copy2(combined_filepath, master_path)
        meta.setdefault("masters", []).append({
            "file": f"master/{master_name}",
            "rows": row_count,
            "saved_at": datetime.now().isoformat(),
            "from_crawl": entry["id"],
        })
        meta["latest_master"] = f"master/{master_name}"

    save_metadata(project_id, meta)
    return dest


def import_file_to_project(
    project_id: str,
    source: Path,
    *,
    subfolder: str = "crawls",
    dest_name: Optional[str] = None,
    crawl_meta: Optional[Dict[str, Any]] = None,
    as_master: bool = False,
) -> Path:
    """Import an existing CSV into a project (migration helper)."""
    if not source.exists():
        raise FileNotFoundError(source)
    dirs = ensure_project_dirs(project_id)
    folder = dirs.get(subfolder, dirs["root"] / subfolder)
    folder.mkdir(parents=True, exist_ok=True)
    name = dest_name or source.name
    dest = folder / name
    if dest.resolve() != source.resolve():
        shutil.copy2(source, dest)

    meta = load_metadata(project_id)
    if crawl_meta:
        meta.setdefault("crawls", []).append(crawl_meta)
    if as_master:
        rel = f"{subfolder}/{name}"
        meta.setdefault("masters", []).append({
            "file": rel,
            "rows": crawl_meta.get("rows") if crawl_meta else None,
            "saved_at": datetime.now().isoformat(),
            "note": "migrated",
        })
        meta["latest_master"] = rel
    save_metadata(project_id, meta)
    return dest


def list_projects(active_only: bool = True) -> List[Dict[str, Any]]:
    """Return projects for UI dropdown (sorted by name)."""
    registry = load_registry()
    categories = registry.get("categories", [])
    out = []
    for pid, meta in registry.get("projects", {}).items():
        if active_only and meta.get("active") is False:
            continue
        cat = meta.get("category", "commercial")
        out.append({
            "project_id": pid,
            "name": meta.get("name", pid),
            "client": meta.get("client", ""),
            "category": cat,
            "label": _project_label(pid, meta),
            "path": f"data/projects/{cat}/{pid}/",
        })
    out.sort(key=lambda x: x["name"].lower())
    return out


def _project_label(project_id: str, meta: Dict[str, Any]) -> str:
    name = meta.get("name", project_id)
    client = meta.get("client", "")
    if client:
        return f"{name} — {client}"
    return name


def register_project(
    *,
    name: str,
    client: str = "",
    category: str = "commercial",
    master_prefix: Optional[str] = None,
    project_id: Optional[str] = None,
    default_keywords: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Create a new project from the UI (updates registry + folders)."""
    registry = load_registry()
    categories = registry.get("categories", ["political", "sme", "agency", "commercial"])
    if category not in categories:
        raise ValueError(f"Invalid category. Choose one of: {', '.join(categories)}")

    name = name.strip()
    if not name:
        raise ValueError("Project name is required")

    pid = project_id.strip() if project_id else _slug(name)
    if not pid:
        raise ValueError("Could not generate project_id — provide a short ID")

    if pid in registry.get("projects", {}):
        raise ValueError(f"Project ID already exists: {pid}")

    prefix = (master_prefix or _slug(name, 30)).strip("_") or pid
    entry = {
        "category": category,
        "name": name,
        "client": client.strip(),
        "master_prefix": prefix,
        "default_keywords": default_keywords or [],
        "active": True,
    }
    registry.setdefault("projects", {})[pid] = entry
    save_registry(registry)

    meta = {
        "project_id": pid,
        "name": name,
        "category": category,
        "client": client.strip(),
        "keywords": default_keywords or [],
        "crawls": [],
        "masters": [],
        "created_at": datetime.now().isoformat(),
    }
    save_metadata(pid, meta)

    return {
        "project_id": pid,
        "label": _project_label(pid, entry),
        "path": str(project_dir(pid)),
        **entry,
    }
