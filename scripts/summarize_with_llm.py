"""LLM 连接池：多 Provider，DeepSeek 优先，其余随机；支持思考模型与并发"""
import json
import os
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from openai import OpenAI

from config import get_data_dir, load_config

# Provider 配置（base_url + model + 思考模型）
PROVIDERS = {
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-chat",
        "reasoner_model": "deepseek-reasoner",
    },
    "qwen": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model": "qwen-turbo",
    },
    "kimi": {
        "base_url": "https://api.moonshot.cn/v1",
        "model": "moonshot-v1-8k",
    },
}

ENV_KEYS = {
    "deepseek": "DEEPSEEK_API_KEY",
    "qwen": "QWEN_API_KEY",
    "kimi": "KIMI_API_KEY",
}


class LLMPool:
    """LLM 连接池：按优先级调用，失败时随机切换"""

    def __init__(self):
        cfg = load_config()
        self.priority = cfg["llm_priority"]
        self.fallback = cfg["llm_fallback"]
        self._use_thinking = cfg.get("use_thinking_model", False)
        self._clients = {}

    def _get_client(self, provider: str) -> OpenAI | None:
        key = ENV_KEYS.get(provider)
        if not key:
            return None
        api_key = os.getenv(key)
        if not api_key:
            return None
        spec = PROVIDERS.get(provider)
        if not spec:
            return None
        return OpenAI(api_key=api_key, base_url=spec["base_url"])

    def _get_model(self, provider: str) -> str:
        spec = PROVIDERS.get(provider, {})
        if getattr(self, "_use_thinking", False) and provider == "deepseek":
            return spec.get("reasoner_model", spec.get("model", "deepseek-chat"))
        return spec.get("model", "gpt-3.5-turbo")

    def _available_order(self) -> list[str]:
        """可用 Provider 顺序：优先 DeepSeek，其余随机"""
        ordered = []
        rest = []
        for p in self.priority:
            if os.getenv(ENV_KEYS.get(p, "")):
                if p == "deepseek":
                    ordered.insert(0, p)
                else:
                    rest.append(p)
        random.shuffle(rest)
        return ordered + rest

    def complete(self, prompt: str, max_retries: int = 3) -> str | None:
        """调用 LLM，失败时切换 Provider"""
        order = self._available_order()
        if not order:
            return None

        last_err = None
        for _ in range(max_retries):
            for provider in order:
                client = self._get_client(provider)
                if not client:
                    continue
                try:
                    max_tok = 1500 if self._use_thinking else 500
                    resp = client.chat.completions.create(
                        model=self._get_model(provider),
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=max_tok,
                    )
                    return resp.choices[0].message.content.strip()
                except Exception as e:
                    last_err = e
                    time.sleep(1)
                    continue
        return None


SUMMARY_PROMPT = """你是一名资深程序员。请根据以下 GitHub 项目信息，用中文输出结构化摘要。

项目名：{name}
描述：{description}
语言：{language}
Stars：{stars}（本周期新增：{current_period_stars}）
链接：{url}

要求：
1. 用发散性思维，从技术特点、行业趋势、用户需求等角度，推导 3-5 个该项目可能的真实应用场景。
2. 每个应用场景一句话，具体可落地。

请严格按以下 JSON 格式输出，不要其他内容：
{{"summary": "一句话解释这个项目是做什么的", "tech_stack": "技术栈/语言", "why_hot": "为什么最近火了", "application_scenarios": "1. 场景一\\n2. 场景二\\n3. 场景三"}}
"""


def summarize_item(item: dict, pool: LLMPool) -> dict:
    """对单个项目生成中文摘要"""
    prompt = SUMMARY_PROMPT.format(
        name=item.get("name", ""),
        description=(item.get("description") or "")[:500],
        language=item.get("language", ""),
        stars=item.get("stars", 0),
        current_period_stars=item.get("currentPeriodStars", 0),
        url=item.get("url", ""),
    )
    result = pool.complete(prompt)
    cfg = load_config()
    fallback = cfg["llm_fallback"]

    if result:
        # 兼容 LLM 返回 ```json ... ``` 包裹
        text = result.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        try:
            parsed = json.loads(text or "{}")
            item["summary_zh"] = parsed.get("summary", item.get("description", ""))
            item["tech_stack"] = parsed.get("tech_stack", item.get("language", ""))
            item["why_hot"] = parsed.get("why_hot", "")
            item["application_scenarios"] = parsed.get("application_scenarios", "")
            return item
        except json.JSONDecodeError:
            item["summary_zh"] = result[:200]
            item["tech_stack"] = item.get("language", "")
            item["why_hot"] = ""
            item["application_scenarios"] = ""
            return item

    if fallback == "raw":
        item["summary_zh"] = item.get("description", "")
        item["tech_stack"] = item.get("language", "")
        item["why_hot"] = ""
        item["application_scenarios"] = ""
        return item

    return None  # skip


def _summarize_one(args):
    """供并发调用的包装"""
    item, pool, key = args
    enriched = summarize_item(item.copy(), pool)
    return (key, enriched)


def run():
    """读取 today.json，为每个项目添加摘要，写回（支持并发）"""
    data_dir = get_data_dir()
    today_path = data_dir / "today.json"

    if not today_path.exists():
        print("today.json 不存在，请先运行 fetch_trending.py")
        return

    cfg = load_config()
    concurrency = cfg.get("llm_concurrency", 10)
    pool = LLMPool()
    data = json.loads(today_path.read_text(encoding="utf-8"))

    # 收集所有待处理项：(period, lang, index)
    tasks = []
    for period in ("daily", "weekly"):
        for lang, items in data.get(period, {}).items():
            for i, item in enumerate(items):
                tasks.append((item, pool, (period, lang, i)))

    # 并发执行
    results = {}
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(_summarize_one, t) for t in tasks]
        for future in as_completed(futures):
            try:
                key, enriched = future.result()
                if enriched is not None:
                    period, lang, i = key
                    if (period, lang) not in results:
                        results[(period, lang)] = {}
                    results[(period, lang)][i] = enriched
            except Exception as e:
                print(f"Warning: summarize failed: {e}")

    # 按原顺序写回
    for period in ("daily", "weekly"):
        for lang, items in data.get(period, {}).items():
            out = []
            for i in range(len(items)):
                if (period, lang) in results and i in results[(period, lang)]:
                    out.append(results[(period, lang)][i])
                else:
                    out.append(items[i])
            data[period][lang] = out

    result = json.dumps(data, ensure_ascii=False, indent=2)
    today_path.write_text(result, encoding="utf-8")
    (data_dir / "weekly.json").write_text(result, encoding="utf-8")

    from datetime import datetime, timezone
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    archive_path = data_dir / "archive" / f"{today}.json"
    archive_path.write_text(result, encoding="utf-8")


if __name__ == "__main__":
    run()
