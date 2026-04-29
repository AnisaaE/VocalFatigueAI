from __future__ import annotations

from pathlib import Path
from typing import Any

from yt_dlp import YoutubeDL


def extract_search_results(keyword: str, max_results: int) -> list[dict[str, Any]]:
    search_query = f"ytsearch{max_results}:{keyword}"
    options = {
        "quiet": True,
        "skip_download": True,
        "extract_flat": True,
        "nocheckcertificate": True,
    }
    with YoutubeDL(options) as ydl:
        info = ydl.extract_info(search_query, download=False)

    entries = info.get("entries") or []
    results: list[dict[str, Any]] = []

    for entry in entries:
        if not entry:
            continue
        results.append(
            {
                "video_id": entry.get("id"),
                "url": entry.get("url") or f"https://www.youtube.com/watch?v={entry.get('id')}",
                "title": entry.get("title"),
                "duration": entry.get("duration"),
                "uploader": entry.get("uploader"),
                "upload_date": entry.get("upload_date"),
                "webpage_url": entry.get("webpage_url"),
            }
        )
    return results


def search_videos(config: dict) -> list[dict[str, Any]]:
    max_total = config.get("max_total_videos", 100)
    per_keyword = config.get("max_videos_per_keyword", 20)
    mode = config.get("search_mode", "combined")
    keywords_by_group = config.get("keyword_groups", {})

    gathered: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    for group_name, keywords in keywords_by_group.items():
        for keyword in keywords:
            results = extract_search_results(keyword, per_keyword)
            for item in results:
                if not item.get("video_id"):
                    continue
                if item["video_id"] in seen_ids:
                    continue
                item["keyword_group"] = group_name
                item["keyword"] = keyword
                item["candidate_type"] = "pending"
                gathered.append(item)
                seen_ids.add(item["video_id"])
                if mode == "combined" and len(gathered) >= max_total:
                    return gathered[:max_total]
            if mode == "per_keyword" and len(results) >= per_keyword and len(gathered) >= per_keyword:
                continue
    if mode == "combined":
        return gathered[:max_total]
    return gathered
