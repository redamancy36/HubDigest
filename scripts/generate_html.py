"""生成前端所需索引文件"""
import json
from pathlib import Path

from config import get_data_dir


def run():
    """生成 archive 索引，供前端历史日期选择器使用"""
    data_dir = get_data_dir()
    archive_dir = data_dir / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)

    # 归档日期列表（供前端加载历史）
    dates = sorted(
        (p.stem for p in archive_dir.glob("*.json")),
        reverse=True,
    )
    index = {"dates": dates}
    (data_dir / "archive-index.json").write_text(
        json.dumps(index, ensure_ascii=False),
        encoding="utf-8",
    )


if __name__ == "__main__":
    run()
