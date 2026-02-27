"""从 GitHub Trending API 抓取趋势项目"""
import json
import re
import time
from pathlib import Path

import requests

from config import get_data_dir, load_config

# API 配置：(base_url, path, params_key_for_language)
# lessx.xyz 实测可用，优先使用
API_SOURCES = [
    ("https://githubtrending.lessx.xyz", "/trending", "language"),  # 优先，返回格式不同
    ("https://github-trending-api.vercel.app", "/repositories", "language"),
    ("https://gh-trending-api.herokuapp.com", "/repositories", "language"),
    ("https://gtrend.yo.fun", "/api/repositories", "language"),
]


def fetch_trending(language: str, since: str) -> list[dict]:
    """获取指定语言和周期的 Trending 项目"""
    cfg = load_config()
    limit = cfg["project_count"]
    results = []

    for base, path, lang_key in API_SOURCES:
        try:
            params = {"since": since}
            if language and language.lower() != "all":
                params[lang_key] = language
            url = f"{base}{path}"
            resp = requests.get(url, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            items = data[:limit] if isinstance(data, list) else data.get("items", [])[:limit]
            for item in items:
                normalized = normalize_item(item, source=base)
                if normalized:
                    results.append(normalized)
            if results:
                return results
        except Exception:
            continue
        time.sleep(0.5)

    return results


def normalize_item(raw: dict, source: str = "") -> dict | None:
    """统一 API 返回格式，兼容 lessx.xyz 及其他源"""
    # lessx.xyz 格式: repository, name, description, language, stars, forks, increased
    if "lessx.xyz" in source:
        url = raw.get("repository", "")
        if not url:
            return None
        full_name = raw.get("name", "")
        parts = full_name.split("/", 1)
        author = parts[0] if len(parts) > 1 else ""
        repo_name = parts[1] if len(parts) > 1 else full_name
        stars_str = str(raw.get("stars", "0")).replace(",", "")
        stars = int(stars_str) if stars_str.isdigit() else 0
        forks_str = str(raw.get("forks", "0")).replace(",", "")
        forks = int(forks_str) if forks_str.isdigit() else 0
        increased = raw.get("increased", "")
        current_stars = 0
        if increased and isinstance(increased, str):
            m = re.search(r"(\d+)\s*stars?", increased, re.I)
            if m:
                current_stars = int(m.group(1))
        return {
            "author": author,
            "name": repo_name,
            "url": url,
            "description": raw.get("description") or "",
            "language": raw.get("language", ""),
            "stars": stars,
            "forks": forks,
            "currentPeriodStars": current_stars,
        }

    # 通用格式
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
    stars = raw.get("stars", raw.get("stargazers_count", 0))
    if isinstance(stars, str):
        stars = int(str(stars).replace(",", "")) if str(stars).replace(",", "").isdigit() else 0
    return {
        "author": str(author),
        "name": str(name),
        "url": url,
        "description": raw.get("description") or "",
        "language": raw.get("language", raw.get("languageColor", "")),
        "stars": stars,
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
