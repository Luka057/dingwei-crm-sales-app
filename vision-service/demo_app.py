"""
demo_app.py — AI 找版 独立 Gradio 演示软件

用途:
    把 vision-service 后端封装成一个浏览器可用的小工具,
    左侧拖图上传, 右侧 top-10 卡片展示, 同货号去重显示最高分.

启动:
    cd vision-service
    source .venv/bin/activate
    VISION_USE_MOCK=false VISION_MODEL_PATH=facebook/dinov2-base \
        python demo_app.py

启动后浏览器自动打开 http://127.0.0.1:7860
"""

from __future__ import annotations

# 标准库
import os
from pathlib import Path

# 第三方
import gradio as gr
from PIL import Image

# 项目内 (复用后端代码, 不通过 HTTP)
from app.config import get_settings
from app.model import build_embedder
from app.vector_store import FaissStore


# ─────────────────────────────────────────────────────────────────
# 启动时一次性加载: 配置 → 嵌入器 → FAISS 索引
# ─────────────────────────────────────────────────────────────────

print("=" * 60)
print("AI 找版 Demo — 启动加载")
print("=" * 60)

settings = get_settings()
print(f"模式: use_mock={settings.use_mock}  model={settings.model_path}")

embedder = build_embedder(settings)
print("✅ 嵌入器加载完成")

store = FaissStore.load(settings.index_path)
INDEX_SIZE = len(store._payloads)
print(f"✅ FAISS 索引加载完成 — 共 {INDEX_SIZE} 条向量")

# 把 corpus 目录的绝对路径算出来, Gradio 要直接读图
CORPUS_DIR = Path(settings.images_dir).resolve()
print(f"图片目录: {CORPUS_DIR}")
print("=" * 60)


# ─────────────────────────────────────────────────────────────────
# 业务逻辑: 单张查询图 → top-10 (同货号去重)
# ─────────────────────────────────────────────────────────────────

def search_topk(query_img: Image.Image, top_k: int = 10):
    """
    入参:
        query_img: 用户上传的查询图 (PIL.Image)
        top_k:     展示几个独立货号 (默认 10)
    返回:
        gallery_items: [(本地图片路径, 标签字符串), ...]  给 gr.Gallery 用
        info_text:     状态信息字符串
    """
    if query_img is None:
        return [], "请先上传一张查询图"

    # 1. 嵌入查询图
    query_img = query_img.convert("RGB")
    q_vec = embedder.embed_image(query_img)

    # 2. ANN 检索: 取 top_k * 6 个候选 (因为每个货号 ≈3 张, 后面要去重)
    candidates = store.search(q_vec, k=top_k * 6)

    # 3. 同货号 (external_id) 去重: 同一个 E0026 只留分数最高的一张
    seen_groups: dict[str, tuple[float, dict]] = {}
    for score, payload in candidates:
        ext_id = payload.get("external_id") or payload.get("sample_no", "")
        if ext_id not in seen_groups or score > seen_groups[ext_id][0]:
            seen_groups[ext_id] = (float(score), payload)

    # 按分数降序取 top_k
    ranked = sorted(seen_groups.values(), key=lambda x: -x[0])[:top_k]

    # 4. 构建 Gallery 入参 (本地图片路径 + 标签)
    gallery_items = []
    for score, payload in ranked:
        img_file = payload.get("image_file", "")
        img_path = CORPUS_DIR / img_file
        label = f"{payload.get('external_id', '?')}  ·  相似度 {score:.3f}"
        gallery_items.append((str(img_path), label))

    info = (
        f"✅ 完成 — 检索 {INDEX_SIZE} 张底图, "
        f"展示 {len(gallery_items)} 个独立货号 (按相似度降序)"
    )
    return gallery_items, info


# ─────────────────────────────────────────────────────────────────
# Gradio UI
# ─────────────────────────────────────────────────────────────────

with gr.Blocks(title="AI 找版 Demo", theme=gr.themes.Soft()) as demo:
    gr.Markdown(
        """
        # 🎀 AI 找版 — Demo

        左侧拖一张织带图进去,右侧会显示**库里最像的 10 个货号**
        (同货号的多张图自动合并,只显示分数最高那张)

        > **模型**: DINOv2-base (DINOv3 审批通过后一行环境变量切换)
        > **底库**: 678 张样板图 / 227 个独立货号
        """
    )

    with gr.Row():
        with gr.Column(scale=1):
            query_input = gr.Image(
                label="拖一张图进来",
                type="pil",
                height=400,
                sources=["upload", "clipboard"],
            )
            top_k_slider = gr.Slider(
                minimum=3, maximum=30, value=10, step=1,
                label="展示几个货号"
            )
            search_btn = gr.Button("🔍 找版", variant="primary", size="lg")

        with gr.Column(scale=2):
            info_box = gr.Markdown("👈 上传图片后,点击「找版」开始检索")
            gallery = gr.Gallery(
                label="Top 货号",
                columns=5,
                rows=2,
                height=600,
                object_fit="cover",
                show_label=True,
            )

    search_btn.click(
        fn=search_topk,
        inputs=[query_input, top_k_slider],
        outputs=[gallery, info_box],
    )


if __name__ == "__main__":
    # 0.0.0.0 = 监听所有接口, 绕开本地代理屏蔽 localhost 的问题
    # show_api=False 避开 Gradio 4.44 + Py3.9 的 schema 解析 bug
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        inbrowser=True,
        show_api=False,
        allowed_paths=[str(CORPUS_DIR)],
    )
