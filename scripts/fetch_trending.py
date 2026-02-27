"""从 GitHub Trending API 抓取趋势项目"""
import json
import time
from pathlib import Path

import requests

from config import get_data_dir, load_config

# 多个 API 源作为 Fallback（社区维护，可能变更）
API_BASES = [
    "https://github-trending-api.vercel.app",
    "https://gh-trending-api.herokuapp.com",
    "https://gtrend.yo.fun",  # /api/repositories
]


def fetch_trending(language: str, since: str) -> list[dict]:
    """获取指定语言和周期的 Trending 项目"""
    cfg = load_config()
    limit = cfg["project_count"]
    results = []

    params_base = {"since": since}
    if language and language.lower() != "all":
        params_base["language"] = language

    for base in API_BASES:
        try:
            path = "/api/repositories" if "yo.fun" in base else "/repositories"
            url = f"{base}{path}"
            resp = requests.get(url, params=params_base, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            # 取前 N 个
            items = data[:limit] if isinstance(data, list) else data.get("items", data)[:limit]
            for item in items:
                results.append(normalize_item(item))
            if results:
                return results
        except Exception:
            continue
        time.sleep(1)

    return results


def normalize_item(raw: dict) -> dict:
    """统一 API 返回格式"""
    owner = raw.get("owner", {})
    author = raw.get("author", raw.get("username", ""))
    if not author and isinstance(owner, dict):
        author = owner.get("login", owner.get("username", ""))
    if isinstance(author, dict):
        author = author.get("username", author.get("login", ""))
    name = raw.get("name", raw.get("repo", ""))
    url = raw.get("url", raw.get("href", f"https://github.com/{author}/{name}"))
    if not url.startswith("http"):
        url = f"https://github.com/{url}"
    return {
        "author": str(author),
        "name": str(name),
        "url": url,
        "description": raw.get("description") or "",
        "language": raw.get("language", raw.get("languageColor", "")),
        "stars": raw.get("stars", raw.get("stargazers_count", 0)),
        "forks": raw.get("forks", raw.get("forks_count", 0)),
        "currentPeriodStars": raw.get("currentPeriodStars", raw.get("stars", 0)),
    }


def run():
    """抓取日榜 + 周榜，多语言，写入 JSON"""
    cfg = load_config()
    data_dir = get_data_dir()
    archive_dir = data_dir / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)

    from datetime import datetime, timezone
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    output = {"date": today, "daily": {}, "weekly": {}}

    for lang in cfg["languages"]:
        output["daily"][lang] = fetch_trending(lang, "daily")
        time.sleep(0.5)
        output["weekly"][lang] = fetch_trending(lang, "weekly")
        time.sleep(0.5)

    # 今日与周榜（主入口）
    (data_dir / "today.json").write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    (data_dir / "weekly.json").write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    # 历史归档
    (archive_dir / f"{today}.json").write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

    # 清理超过 30 天的归档
    archives = sorted(archive_dir.glob("*.json"), key=lambda p: p.stem, reverse=True)
    for old in archives[30:]:
        old.unlink()

    return output


if __name__ == "__main__":
    run()
