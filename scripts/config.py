"""HubDigest 配置加载"""
import os
from pathlib import Path

import yaml

# 项目根目录
ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config.yaml"
    

def load_config():
    """加载 config.yaml，环境变量可覆盖"""
    with open(CONFIG_PATH, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    return {
        "project_count": int(os.getenv("PROJECT_COUNT", cfg.get("project_count", 20))),
        "languages": cfg.get("languages", ["all"]),
        "llm_priority": cfg.get("llm_priority", ["deepseek"]),
        "readme_max_chars": int(cfg.get("readme_max_chars", 1500)),
        "llm_fallback": cfg.get("llm_fallback", "raw"),
        "llm_concurrency": int(os.getenv("LLM_CONCURRENCY", cfg.get("llm_concurrency", 50))),
        "use_thinking_model": cfg.get("use_thinking_model", False),
    }


def get_data_dir():
    """数据输出目录（与 index.html 同层级，便于静态托管）"""
    d = ROOT / "src" / "data"
    d.mkdir(parents=True, exist_ok=True)
    return d
