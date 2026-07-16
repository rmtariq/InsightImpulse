#!/usr/bin/env python3
"""Route crawled media through Nemotron NIM and attach derived text.

This script is intentionally placed between crawler output and the existing
Malay BERT sentiment processor.  Its contract is simple: media becomes text;
all downstream CSV/JSON formats remain compatible with the current pipeline.

Examples:
  python scripts/multimodal_router.py \
    --input data/smart_crawlers/tiktok/items.json \
    --output data/smart_crawlers/tiktok/items_routed.json

  python scripts/multimodal_router.py \
    --input data/smart_crawlers/tiktok/tiktok_prn.csv \
    --output data/smart_crawlers/tiktok/tiktok_prn_routed.csv \
    --merge-text
"""
from __future__ import annotations

import argparse
import base64
import csv
import json
import mimetypes
import os
import re
import sys
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse

import requests

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.nim_client import get_project_config, project_multimodal_enabled  # noqa: E402


DEFAULT_HOSTED_URL = os.getenv("NIM_LLM_BASE_URL", "http://localhost:8000/v1")
OMNI_URL = os.getenv("NIM_OMNI_URL", DEFAULT_HOSTED_URL if DEFAULT_HOSTED_URL.startswith("https://") else "http://localhost:8002")
OCR_URL = os.getenv("NIM_OCR_URL", DEFAULT_HOSTED_URL if DEFAULT_HOSTED_URL.startswith("https://") else "http://localhost:8004")
ASR_URL = os.getenv("NIM_ASR_URL", DEFAULT_HOSTED_URL if DEFAULT_HOSTED_URL.startswith("https://") else "http://localhost:9000")
NIM_API_KEY = os.getenv("NIM_LLM_API_KEY") or os.getenv("NVIDIA_API_KEY") or ""

OMNI_MODEL = os.getenv("NIM_OMNI_MODEL", "nemotron-3-nano-omni-30b-a3b-reasoning")
OCR_MODEL = os.getenv("NIM_OCR_MODEL", "nemotron-ocr-v2")
ASR_MODEL = os.getenv("NIM_ASR_MODEL", "nvidia/parakeet-1.1b-rnnt-multilingual-asr")

VIDEO_EXTS = {".mp4", ".mov", ".webm", ".avi", ".mkv"}
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"}
AUDIO_EXTS = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"}

MEDIA_FIELDS = (
    "media_url",
    "video_url",
    "image_url",
    "audio_url",
    "thumbnail_url",
    "attachment_url",
    "url",
)
TEXT_FIELDS = ("post_text", "text", "content", "caption", "description", "Text")

PLATFORM_VIDEO_PATTERNS = (
    re.compile(r"youtube\.com/watch", re.I),
    re.compile(r"youtu\.be/", re.I),
    re.compile(r"tiktok\.com/.+/video/", re.I),
    re.compile(r"facebook\.com/.+/videos/", re.I),
    re.compile(r"fb\.watch/", re.I),
)

DIRECT_VIDEO_FIELDS = (
    "video_url",
    "media_url",
    "videoDownloadUrl",
    "downloadAddr",
    "playAddr",
    "videoMeta",
)

THUMBNAIL_FIELDS = (
    "thumbnail_url",
    "video_thumbnail",
    "thumbnail",
    "cover",
    "covers",
    "image",
)


def _is_platform_video_url(url: str) -> bool:
    return bool(url) and any(pattern.search(url) for pattern in PLATFORM_VIDEO_PATTERNS)


def _is_video_post(item: dict[str, Any]) -> bool:
    item_type = str(item.get("Type") or item.get("type") or "post").lower()
    if item_type == "comment":
        return False
    platform = str(item.get("Platform") or item.get("platform") or "").lower()
    if platform in {"youtube", "tiktok"}:
        return True
    page_url = str(item.get("URL") or item.get("url") or "").strip()
    if _is_platform_video_url(page_url):
        return True
    if str(item.get("media_type") or "").lower() == "video":
        return True
    return bool(item.get("video_url") or item.get("video_files"))


def _first_url(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        for entry in value:
            if isinstance(entry, str) and entry.strip():
                return entry.strip()
            if isinstance(entry, dict):
                for key in ("url", "uri", "downloadURL", "download_url", "file"):
                    candidate = str(entry.get(key) or "").strip()
                    if candidate.startswith(("http://", "https://")):
                        return candidate
    if isinstance(value, dict):
        for key in ("url", "uri", "downloadURL", "download_url", "file"):
            candidate = str(value.get(key) or "").strip()
            if candidate.startswith(("http://", "https://")):
                return candidate
    return ""


def _extract_direct_video_url(item: dict[str, Any]) -> str:
    video_files = item.get("video_files")
    if isinstance(video_files, list):
        best = ""
        best_quality = -1
        for entry in video_files:
            if not isinstance(entry, dict):
                continue
            candidate = _first_url(entry)
            if not candidate:
                continue
            quality = int(entry.get("quality") or entry.get("height") or 0)
            if quality >= best_quality:
                best = candidate
                best_quality = quality
        if best:
            return best

    video_meta = item.get("videoMeta")
    if isinstance(video_meta, dict):
        for key in ("downloadAddr", "playAddr", "videoUrl", "url"):
            candidate = _first_url(video_meta.get(key))
            if candidate:
                return candidate

    for field in DIRECT_VIDEO_FIELDS:
        candidate = _first_url(item.get(field))
        if candidate and (_clean_ext(candidate) in VIDEO_EXTS or "video" in candidate.lower()):
            return candidate
    return ""


def _extract_thumbnail_url(item: dict[str, Any]) -> str:
    for field in THUMBNAIL_FIELDS:
        candidate = _first_url(item.get(field))
        if candidate.startswith(("http://", "https://")):
            return candidate
    return ""


def _page_url(item: dict[str, Any]) -> str:
    return str(item.get("URL") or item.get("url") or "").strip()


def _youtube_video_id(url: str) -> str:
    parsed = urlparse(url)
    if "youtu.be" in parsed.netloc:
        return parsed.path.strip("/").split("/")[0]
    if "youtube.com" in parsed.netloc:
        if parsed.path.startswith("/watch"):
            query = parsed.query or ""
            for part in query.split("&"):
                if part.startswith("v="):
                    return part.split("=", 1)[1]
        if parsed.path.startswith("/shorts/"):
            return parsed.path.split("/shorts/")[-1].split("/")[0]
    return ""


def _infer_thumbnail_url(item: dict[str, Any]) -> str:
    thumbnail = _extract_thumbnail_url(item)
    if thumbnail:
        return thumbnail
    page_url = _page_url(item)
    if not page_url:
        return ""
    video_id = _youtube_video_id(page_url)
    if video_id:
        return f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
    if "tiktok.com" in page_url.lower():
        try:
            response = requests.get(
                "https://www.tiktok.com/oembed",
                params={"url": page_url},
                timeout=15,
                headers={"User-Agent": "InsightPulse/1.0"},
            )
            if response.ok:
                return str(response.json().get("thumbnail_url") or "").strip()
        except Exception:
            return ""
    return ""


def _load_env() -> None:
    env = ROOT / ".env"
    if not env.exists():
        return
    for line in env.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


def _media_path(item: dict[str, Any]) -> str:
    for field in MEDIA_FIELDS:
        value = str(item.get(field) or "").strip()
        if value:
            return value
    return ""


def _clean_ext(path_or_url: str) -> str:
    parsed = urlparse(path_or_url)
    path = parsed.path if parsed.scheme else path_or_url
    return Path(path).suffix.lower()


def is_media(item: dict[str, Any]) -> bool:
    direct = _extract_direct_video_url(item)
    if direct and (_clean_ext(direct) in VIDEO_EXTS | IMAGE_EXTS | AUDIO_EXTS):
        return True
    if _extract_thumbnail_url(item) and _is_video_post(item):
        return True
    if _infer_thumbnail_url(item) and _is_video_post(item):
        return True
    media = _media_path(item)
    ext = _clean_ext(media)
    if ext in VIDEO_EXTS | IMAGE_EXTS | AUDIO_EXTS:
        return True
    return _is_video_post(item) and bool(_page_url(item))


def _b64(path: str) -> str:
    return base64.b64encode(Path(path).read_bytes()).decode("utf-8")


def _data_url(path: str, fallback_mime: str) -> str:
    mime = mimetypes.guess_type(path)[0] or fallback_mime
    return f"data:{mime};base64,{_b64(path)}"


def _media_payload_url(path_or_url: str, fallback_mime: str) -> str:
    if path_or_url.startswith(("http://", "https://", "data:")):
        return path_or_url
    return _data_url(path_or_url, fallback_mime)


def _headers() -> dict[str, str]:
    if not NIM_API_KEY or NIM_API_KEY == "nvapi-local-not-used":
        return {}
    return {"Authorization": f"Bearer {NIM_API_KEY}"}


def _v1_url(base_url: str, path: str) -> str:
    """Join hosted/local NIM URLs without duplicating /v1."""
    base = base_url.rstrip("/")
    if base.endswith("/v1"):
        return f"{base}/{path.lstrip('/')}"
    return f"{base}/v1/{path.lstrip('/')}"


def process_video_page_context(
    *,
    page_url: str,
    thumbnail_url: str = "",
    caption: str = "",
    timeout: int = 180,
) -> str:
    """Hosted-safe fallback when only a social page URL is available."""
    image_url = thumbnail_url.strip()
    if not image_url:
        raise ValueError(f"No thumbnail available for video page: {page_url}")

    prompt = (
        "You are analysing Malaysian political social video content. "
        f"Video page: {page_url}\n"
        f"Caption/description: {caption or '(none)'}\n\n"
        "From the thumbnail and caption, infer likely spoken themes, on-screen text, "
        "visual cues, and political sentiment. Include BM/English/中文/Tamil terms if visible. "
        "Output plain text only."
    )
    payload = {
        "model": OCR_MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": _media_payload_url(image_url, "image/jpeg")}},
                    {"type": "text", "text": prompt},
                ],
            }
        ],
        "temperature": 0.1,
    }
    response = requests.post(_v1_url(OCR_URL, "chat/completions"), headers=_headers(), json=payload, timeout=timeout)
    _raise_for_status(response, "vision-page", OCR_MODEL)
    return response.json()["choices"][0]["message"]["content"].strip()


def process_video(path_or_url: str, timeout: int = 300) -> str:
    """Use Nemotron Omni for transcript + visual description."""
    payload = {
        "model": OMNI_MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "video_url", "video_url": {"url": _media_payload_url(path_or_url, "video/mp4")}},
                    {
                        "type": "text",
                        "text": (
                            "Transcribe all spoken content in Bahasa Melayu, English, Mandarin, Cantonese, "
                            "or Tamil. Then describe important visual scenes and on-screen text. "
                            "Output plain text only."
                        ),
                    },
                ],
            }
        ],
        "temperature": 0.2,
    }
    response = requests.post(_v1_url(OMNI_URL, "chat/completions"), headers=_headers(), json=payload, timeout=timeout)
    _raise_for_status(response, "omni", OMNI_MODEL)
    return response.json()["choices"][0]["message"]["content"].strip()


def process_image(path_or_url: str, timeout: int = 120) -> str:
    """Use Nemotron OCR for screenshots, posters, memes, and infographics."""
    payload = {
        "model": OCR_MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": _media_payload_url(path_or_url, "image/jpeg")}},
                    {
                        "type": "text",
                        "text": (
                            "Extract all visible text exactly as written, preserving language "
                            "(BM, English, 中文, Tamil). Output plain text only."
                        ),
                    },
                ],
            }
        ],
        "temperature": 0.0,
    }
    response = requests.post(_v1_url(OCR_URL, "chat/completions"), headers=_headers(), json=payload, timeout=timeout)
    _raise_for_status(response, "ocr", OCR_MODEL)
    return response.json()["choices"][0]["message"]["content"].strip()


def process_audio(path_or_url: str, timeout: int = 180) -> str:
    """Use Nemotron ASR HTTP endpoint for multilingual speech-to-text."""
    audio = requests.get(path_or_url, timeout=timeout).content if path_or_url.startswith(("http://", "https://")) else Path(path_or_url).read_bytes()
    filename = Path(urlparse(path_or_url).path).name or "clip.wav"
    response = requests.post(
        _v1_url(ASR_URL, "audio/transcriptions"),
        headers=_headers(),
        files={"audio": (filename, audio)},
        data={"model": ASR_MODEL},
        timeout=timeout,
    )
    _raise_for_status(response, "asr", ASR_MODEL)
    return str(response.json().get("text", "")).strip()


def _raise_for_status(response: requests.Response, route: str, model: str) -> None:
    if response.ok:
        return
    body = response.text[:1000]
    raise requests.HTTPError(
        f"{route} request failed: HTTP {response.status_code} model={model} url={response.url} body={body}",
        response=response,
    )


def _existing_text(item: dict[str, Any]) -> str:
    for field in TEXT_FIELDS:
        value = str(item.get(field) or "").strip()
        if value:
            return value
    return ""


def route_item(item: dict[str, Any], *, merge_text: bool = False) -> dict[str, Any]:
    """Populate ``derived_text`` for media rows. Text-only rows pass through."""
    if item.get("derived_text"):
        if merge_text:
            _merge_text(item)
        return item

    direct_video = _extract_direct_video_url(item)
    thumbnail = _infer_thumbnail_url(item)
    page_url = _page_url(item)
    caption = _existing_text(item)

    try:
        if direct_video and _clean_ext(direct_video) in VIDEO_EXTS:
            item["derived_text"] = process_video(direct_video)
            item["derived_text_source"] = "nemotron-omni"
        elif direct_video:
            item["derived_text"] = process_video(direct_video)
            item["derived_text_source"] = "nemotron-omni"
        elif _is_video_post(item) and thumbnail:
            item["derived_text"] = process_video_page_context(
                page_url=page_url or thumbnail,
                thumbnail_url=thumbnail,
                caption=caption,
            )
            item["derived_text_source"] = "nemotron-vl-thumbnail"
        elif _is_video_post(item) and page_url:
            item["derived_text"] = process_video(page_url)
            item["derived_text_source"] = "nemotron-omni"
        else:
            media = _media_path(item)
            ext = _clean_ext(media)
            if not media or ext not in VIDEO_EXTS | IMAGE_EXTS | AUDIO_EXTS:
                return item
            if ext in VIDEO_EXTS:
                item["derived_text"] = process_video(media)
                item["derived_text_source"] = "nemotron-omni"
            elif ext in IMAGE_EXTS:
                item["derived_text"] = process_image(media)
                item["derived_text_source"] = "nemotron-ocr"
            elif ext in AUDIO_EXTS:
                item["derived_text"] = process_audio(media)
                item["derived_text_source"] = "nemotron-asr"
        if merge_text:
            _merge_text(item)
    except Exception as exc:
        item["derived_error"] = str(exc)
    return item


def _merge_text(item: dict[str, Any]) -> None:
    derived = str(item.get("derived_text") or "").strip()
    if not derived:
        return
    original = _existing_text(item)
    merged = f"{original}\n\n[Derived media text]\n{derived}".strip() if original else derived
    target_field = next((field for field in TEXT_FIELDS if field in item), "post_text")
    item[target_field] = merged


def _read_json(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        if isinstance(payload.get("items"), list):
            return [dict(item) for item in payload["items"]]
        return [payload]
    if isinstance(payload, list):
        return [dict(item) for item in payload]
    raise ValueError("JSON input must be an object, an object with items[], or a list")


def _write_json(path: Path, items: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")


def _read_csv(path: Path) -> list[dict[str, Any]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return [dict(row) for row in csv.DictReader(f)]


def _write_csv(path: Path, items: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    for item in items:
        for key in item.keys():
            if key not in fields:
                fields.append(key)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(items)


def _load_items(path: Path) -> list[dict[str, Any]]:
    if path.suffix.lower() == ".csv":
        return _read_csv(path)
    return _read_json(path)


def _save_items(path: Path, items: list[dict[str, Any]]) -> None:
    if path.suffix.lower() == ".csv":
        _write_csv(path, items)
    else:
        _write_json(path, items)


def route_items(items: Iterable[dict[str, Any]], *, merge_text: bool = False, limit: int = 0) -> list[dict[str, Any]]:
    routed: list[dict[str, Any]] = []
    media_seen = 0
    for item in items:
        should_process = is_media(item)
        if should_process:
            media_seen += 1
        if limit and should_process and media_seen > limit:
            routed.append(item)
            continue
        routed.append(route_item(item, merge_text=merge_text))
    return routed


def main() -> int:
    _load_env()
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Input JSON/CSV from data/smart_crawlers/{platform}/")
    parser.add_argument("--output", required=True, help="Output JSON/CSV with derived_text")
    parser.add_argument("--project-id", default=None, help="Project registry key for multimodal flag")
    parser.add_argument("--force", action="store_true", help="Run even if project registry multimodal=false")
    parser.add_argument("--merge-text", action="store_true", help="Append derived_text into the main text field for immediate sentiment processing")
    parser.add_argument("--limit", type=int, default=0, help="Process only the first N media rows; 0 means all")
    args = parser.parse_args()

    if args.project_id and not args.force and not project_multimodal_enabled(args.project_id):
        project = get_project_config(args.project_id)
        print(f"Multimodal disabled for {args.project_id} ({project.get('name', 'unknown project')}); use --force to override.")
        return 0

    input_path = Path(args.input)
    output_path = Path(args.output)
    items = _load_items(input_path)
    routed = route_items(items, merge_text=args.merge_text, limit=args.limit)
    _save_items(output_path, routed)

    media_total = sum(1 for item in routed if is_media(item))
    routed_ok = sum(1 for item in routed if item.get("derived_text"))
    routed_err = sum(1 for item in routed if item.get("derived_error"))
    print(
        f"Routed {len(routed)} rows → {routed_ok}/{media_total} media rows derived "
        f"({routed_err} errors). Output: {output_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
