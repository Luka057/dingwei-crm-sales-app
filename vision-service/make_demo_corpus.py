"""
make_demo_corpus.py — 生成演示语料库（合成图片 + CSV 清单）。

用途:
  无需真实样本图片即可验证 vision-service 的完整管道:
  1. 运行此脚本 → 生成 ./corpus/*.png + ./samples.csv
  2. python index_samples.py --manifest samples.csv --images ./corpus --out ./index
  3. uvicorn app.main:app --port 8077
  4. curl 测试

生成内容:
  8 张合成 PNG（纯色 + 条纹，视觉上不同）
  8 行 CSV，包含真实的织带元数据字段
  sample_no 格式: HY-{宽度}-{颜色缩写}-{张力}
"""

import csv
import os
from PIL import Image, ImageDraw

# ─────────────────────────────────────────────────────────────────
# 目录配置
# ─────────────────────────────────────────────────────────────────

CORPUS_DIR = "./corpus"
CSV_PATH = "./samples.csv"
IMG_SIZE = (224, 224)  # 与 SigLIP 默认输入尺寸一致

# ─────────────────────────────────────────────────────────────────
# 样本定义
# 字段对应 MANIFEST_FORMAT.md 中的 8 列
# status 使用拼音枚举: qiyang / zhongban / queren / yizhuandingdan / yifangqi
# ─────────────────────────────────────────────────────────────────

SAMPLES = [
    {
        "image_file": "sample_001.png",
        "sample_no": "HY-20-BK-soft",
        "external_id": "ERP-10001",
        "width": "20mm",
        "tension": "soft",
        "ribbon_type": "提花织带",
        "color": "黑色",
        "status": "queren",
        # 图片生成参数
        "_style": "solid",
        "_bg": (20, 20, 20),            # 深黑
    },
    {
        "image_file": "sample_002.png",
        "sample_no": "HY-25-WH-medium",
        "external_id": "ERP-10002",
        "width": "25mm",
        "tension": "medium",
        "ribbon_type": "提花织带",
        "color": "白色",
        "status": "yizhuandingdan",
        "_style": "solid",
        "_bg": (240, 240, 240),         # 浅白
    },
    {
        "image_file": "sample_003.png",
        "sample_no": "HY-30-RD-hard",
        "external_id": "ERP-10003",
        "width": "30mm",
        "tension": "hard",
        "ribbon_type": "平纹织带",
        "color": "红色",
        "status": "zhongban",
        "_style": "stripe",
        "_bg": (200, 30, 30),           # 红色条纹
        "_stripe": (255, 200, 200),
    },
    {
        "image_file": "sample_004.png",
        "sample_no": "HY-20-BL-soft",
        "external_id": "ERP-10004",
        "width": "20mm",
        "tension": "soft",
        "ribbon_type": "平纹织带",
        "color": "蓝色",
        "status": "qiyang",
        "_style": "stripe",
        "_bg": (30, 80, 200),           # 蓝色条纹
        "_stripe": (180, 210, 255),
    },
    {
        "image_file": "sample_005.png",
        "sample_no": "HY-38-GN-medium",
        "external_id": "ERP-10005",
        "width": "38mm",
        "tension": "medium",
        "ribbon_type": "罗纹织带",
        "color": "绿色",
        "status": "queren",
        "_style": "horizontal_stripe",
        "_bg": (30, 160, 60),           # 绿色横纹
        "_stripe": (180, 240, 180),
    },
    {
        "image_file": "sample_006.png",
        "sample_no": "HY-15-YL-soft",
        "external_id": "ERP-10006",
        "width": "15mm",
        "tension": "soft",
        "ribbon_type": "提花织带",
        "color": "黄色",
        "status": "yifangqi",
        "_style": "solid",
        "_bg": (230, 200, 30),          # 黄色
    },
    {
        "image_file": "sample_007.png",
        "sample_no": "HY-50-GY-hard",
        "external_id": "ERP-10007",
        "width": "50mm",
        "tension": "hard",
        "ribbon_type": "锦纶织带",
        "color": "灰色",
        "status": "zhongban",
        "_style": "checker",
        "_bg": (180, 180, 180),         # 灰色棋盘格
        "_stripe": (120, 120, 120),
    },
    {
        "image_file": "sample_008.png",
        "sample_no": "HY-25-PP-medium",
        "external_id": "ERP-10008",
        "width": "25mm",
        "tension": "medium",
        "ribbon_type": "锦纶织带",
        "color": "紫色",
        "status": "qiyang",
        "_style": "stripe",
        "_bg": (120, 40, 180),          # 紫色条纹
        "_stripe": (220, 180, 255),
    },
]

# CSV 列顺序（与 MANIFEST_FORMAT.md 一致）
CSV_COLUMNS = [
    "image_file", "sample_no", "external_id",
    "width", "tension", "ribbon_type", "color", "status",
]


# ─────────────────────────────────────────────────────────────────
# 图片生成函数
# ─────────────────────────────────────────────────────────────────

def make_solid(size: tuple[int, int], color: tuple[int, int, int]) -> Image.Image:
    """生成纯色图片。"""
    return Image.new("RGB", size, color)


def make_vertical_stripe(
    size: tuple[int, int],
    color1: tuple[int, int, int],
    color2: tuple[int, int, int],
    stripe_width: int = 20,
) -> Image.Image:
    """生成垂直条纹图片。"""
    img = Image.new("RGB", size, color1)
    draw = ImageDraw.Draw(img)
    w, h = size
    x = 0
    toggle = False
    while x < w:
        if toggle:
            draw.rectangle([x, 0, x + stripe_width - 1, h], fill=color2)
        x += stripe_width
        toggle = not toggle
    return img


def make_horizontal_stripe(
    size: tuple[int, int],
    color1: tuple[int, int, int],
    color2: tuple[int, int, int],
    stripe_height: int = 18,
) -> Image.Image:
    """生成水平条纹图片。"""
    img = Image.new("RGB", size, color1)
    draw = ImageDraw.Draw(img)
    w, h = size
    y = 0
    toggle = False
    while y < h:
        if toggle:
            draw.rectangle([0, y, w, y + stripe_height - 1], fill=color2)
        y += stripe_height
        toggle = not toggle
    return img


def make_checker(
    size: tuple[int, int],
    color1: tuple[int, int, int],
    color2: tuple[int, int, int],
    cell_size: int = 28,
) -> Image.Image:
    """生成棋盘格图片。"""
    img = Image.new("RGB", size, color1)
    draw = ImageDraw.Draw(img)
    w, h = size
    for row in range(0, h, cell_size):
        for col in range(0, w, cell_size):
            if (row // cell_size + col // cell_size) % 2 == 1:
                draw.rectangle(
                    [col, row, col + cell_size - 1, row + cell_size - 1],
                    fill=color2,
                )
    return img


def generate_image(sample: dict) -> Image.Image:
    """根据样本的 _style 参数生成对应图片。"""
    style = sample["_style"]
    bg = sample["_bg"]
    stripe = sample.get("_stripe", (255, 255, 255))

    if style == "solid":
        return make_solid(IMG_SIZE, bg)
    elif style == "stripe":
        return make_vertical_stripe(IMG_SIZE, bg, stripe, stripe_width=22)
    elif style == "horizontal_stripe":
        return make_horizontal_stripe(IMG_SIZE, bg, stripe, stripe_height=18)
    elif style == "checker":
        return make_checker(IMG_SIZE, bg, stripe, cell_size=28)
    else:
        return make_solid(IMG_SIZE, bg)


# ─────────────────────────────────────────────────────────────────
# 主函数
# ─────────────────────────────────────────────────────────────────

def main() -> None:
    # 创建语料库目录
    os.makedirs(CORPUS_DIR, exist_ok=True)
    print(f"[demo] 图片目录: {os.path.abspath(CORPUS_DIR)}")

    # 生成图片
    for sample in SAMPLES:
        img = generate_image(sample)
        out_path = os.path.join(CORPUS_DIR, sample["image_file"])
        img.save(out_path)
        print(f"[demo] 生成图片: {out_path} ({sample['_style']}, {sample['color']})")

    # 写 CSV
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for sample in SAMPLES:
            # 只写 CSV 需要的字段（去掉内部 _style/_bg/_stripe 字段）
            row = {k: sample[k] for k in CSV_COLUMNS}
            writer.writerow(row)

    print(f"[demo] CSV 清单: {os.path.abspath(CSV_PATH)}（{len(SAMPLES)} 行）")
    print()
    print("下一步:")
    print("  python index_samples.py --manifest samples.csv --images ./corpus --out ./index")
    print("  uvicorn app.main:app --host 127.0.0.1 --port 8077")


if __name__ == "__main__":
    main()
