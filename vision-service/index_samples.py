"""
index_samples.py — 离线索引构建脚本（CLI）。

用法:
  python index_samples.py \
    --manifest samples.csv \
    --images   ./corpus \
    --out      ./index

CSV 格式（见 MANIFEST_FORMAT.md）:
  image_file, sample_no, external_id, width, tension, ribbon_type, color, status

处理流程:
  1. 读取 CSV，逐行加载图片
  2. embed_image → FAISS 存储图片向量
  3. 根据字段生成文字描述 caption → embed_text → 存入 payload (text_emb)
  4. 保存索引到 --out 目录

注意:
  - 如果图片文件不存在，该行会跳过（打印警告）
  - 大规模语料建议开多进程 + GPU，这里是单进程 CPU 版
"""

import argparse
import csv
import logging
import os
import sys

from PIL import Image

# 将 vision-service 目录加入 sys.path，以便直接运行此脚本
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

from app.config import get_settings
from app.model import build_embedder
from app.vector_store import FaissStore

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


# CSV 必需字段
REQUIRED_COLUMNS = {
    "image_file", "sample_no", "external_id",
    "width", "tension", "ribbon_type", "color", "status",
}


def build_caption(row: dict) -> str:
    """
    根据 CSV 行构建文字描述，作为文本嵌入的输入。

    例: "提花织带，黑色，20mm，开力度soft"
    缺失字段自动跳过。
    """
    parts = []
    if row.get("ribbon_type"):
        parts.append(row["ribbon_type"])
    if row.get("color"):
        parts.append(row["color"])
    if row.get("width"):
        parts.append(row["width"])
    if row.get("tension"):
        parts.append(f"开力度{row['tension']}")
    return "，".join(parts) if parts else row.get("sample_no", "")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="构建 vision-service 向量索引",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python index_samples.py --manifest samples.csv --images ./corpus --out ./index
  VISION_USE_MOCK=false python index_samples.py ...  # 真实 SigLIP 模式
        """,
    )
    parser.add_argument(
        "--manifest",
        required=True,
        help="CSV 样本清单文件路径（见 MANIFEST_FORMAT.md）",
    )
    parser.add_argument(
        "--images",
        required=True,
        help="图片文件所在目录",
    )
    parser.add_argument(
        "--out",
        required=True,
        help="输出索引目录（将写入 index.faiss + metadata.json）",
    )
    args = parser.parse_args()

    # ── 加载配置和嵌入器 ─────────────────────────────────────────
    settings = get_settings()
    embedder = build_embedder(settings)

    store = FaissStore(embed_dim=settings.embed_dim)

    # ── 读取 CSV ─────────────────────────────────────────────────
    if not os.path.exists(args.manifest):
        logger.error("找不到 CSV 文件: %s", args.manifest)
        sys.exit(1)

    with open(args.manifest, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        logger.error("CSV 文件为空或无数据行: %s", args.manifest)
        sys.exit(1)

    # 检查必需字段
    actual_cols = set(rows[0].keys())
    missing = REQUIRED_COLUMNS - actual_cols
    if missing:
        logger.warning("CSV 缺少字段（将以空字符串处理）: %s", missing)

    # ── 逐行索引 ─────────────────────────────────────────────────
    indexed = 0
    skipped = 0

    for i, row in enumerate(rows, start=1):
        image_file = row.get("image_file", "").strip()
        sample_no = row.get("sample_no", f"row_{i}").strip()
        image_path = os.path.join(args.images, image_file)

        # 检查图片文件
        if not image_file:
            logger.warning("[row %d] image_file 为空，跳过", i)
            skipped += 1
            continue

        if not os.path.exists(image_path):
            logger.warning("[row %d] 图片文件不存在: %s，跳过", i, image_path)
            skipped += 1
            continue

        # 加载图片并计算嵌入
        try:
            img = Image.open(image_path).convert("RGB")
            img_emb = embedder.embed_image(img)              # 图片向量 → 存入 FAISS

            caption = build_caption(row)
            txt_emb = embedder.embed_text(caption)           # 文本向量 → 存入 payload

        except Exception as exc:
            logger.warning("[row %d] %s 处理失败: %s，跳过", i, sample_no, exc)
            skipped += 1
            continue

        # 构建 payload（随向量一起存储，检索时返回）
        payload = {
            "sample_no": sample_no,
            "external_id": row.get("external_id", "").strip() or None,
            "image_file": image_file,
            "text_emb": txt_emb.tolist(),          # numpy → list，方便 JSON 序列化
            "metadata": {
                "width": row.get("width", "").strip(),
                "tension": row.get("tension", "").strip(),
                "ribbon_type": row.get("ribbon_type", "").strip(),
                "color": row.get("color", "").strip(),
                "status": row.get("status", "").strip(),
            },
        }

        import numpy as np
        store.add(img_emb.reshape(1, -1), [payload])         # 添加到 FAISS
        indexed += 1
        logger.info("[index] %d/%d — %s (%s)", i, len(rows), sample_no, image_file)

    # ── 保存索引 ─────────────────────────────────────────────────
    if indexed == 0:
        logger.error("没有成功索引任何样本（跳过 %d 行），索引未写入", skipped)
        sys.exit(1)

    store.save(args.out)
    print(f"[index] {indexed} samples indexed → {args.out}")

    if skipped:
        logger.warning("[index] 跳过了 %d 行（图片不存在或处理失败）", skipped)


if __name__ == "__main__":
    main()
