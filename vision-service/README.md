# vision-service — 鼎伟 CRM "AI 找板" 视觉服务

## 概述

本服务为"AI 找板"功能提供样本相似图检索能力：
- **图片向量**：用 SigLIP2 编码查询图和样本图，计算视觉相似度
- **文字向量**：用同一模型编码描述文字，计算语义相似度
- **工艺匹配**：精确比对宽度/张力/类型等参数
- **三路融合**：加权合并为最终排序分数

---

## 快速开始（本地 Mock 模式，无需 GPU/大模型）

```bash
# 1. 进入目录
cd vision-service/

# 2. 创建虚拟环境并安装依赖（约 1-2 分钟）
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 3. 生成演示语料库（8 张合成图片 + samples.csv）
python make_demo_corpus.py

# 4. 构建向量索引
python index_samples.py --manifest samples.csv --images ./corpus --out ./index

# 5. 启动服务
uvicorn app.main:app --host 127.0.0.1 --port 8077

# 6. 测试健康检查
curl http://127.0.0.1:8077/health
# → {"ok": true, "mode": "mock", "indexed": 8, ...}

# 7. 测试图片检索（用第一张演示图）
python -c "
import base64, glob, json, urllib.request
b = base64.b64encode(open(sorted(glob.glob('corpus/*.png'))[0],'rb').read()).decode()
req = json.dumps({'image_base64': b, 'description': '提花织带 黑色',
                  'filters': {'ribbon_type': '提花织带'}, 'top_k': 3}).encode()
r = urllib.request.urlopen(urllib.request.Request(
    'http://127.0.0.1:8077/sample-search', data=req,
    headers={'Content-Type': 'application/json'}))
print(r.read().decode()[:800])
"
```

---

## Mock 模式 vs 真实 SigLIP2 模式

### Mock 模式（默认，`VISION_USE_MOCK=true`）

- **无需** torch / transformers / GPU
- 向量由 SHA-256 哈希生成（确定性，但无真实语义）
- 视觉上相似的图片**不会**在向量空间中聚类（只是验证管道）
- 适合：开发调试、CI 测试、展示管道

### 真实 SigLIP2 模式（`VISION_USE_MOCK=false`）

```bash
# 额外安装（约 3-6 GB 下载）
pip install torch transformers

# 启动（会自动下载模型，首次需要网络）
VISION_USE_MOCK=false uvicorn app.main:app --port 8077

# 或指定本地权重目录
VISION_USE_MOCK=false VISION_MODEL_PATH=/path/to/siglip2 uvicorn app.main:app --port 8077
```

**Apple Silicon（M1/M2/M3）原生 MPS 加速**：直接用 `uvicorn` 运行（非 Docker），
设备自动选择 `mps`，速度远快于 CPU。

**Docker 部署**：Linux 容器内没有 MPS，始终使用 CPU 推理。

---

## 算法工程师交接线（ENGINEER SEAM）

### 替换嵌入模型 — `app/model.py`

```
app/model.py
└── class SiglipEmbedder
    ├── __init__: 模型加载（标注 ENGINEER SEAM 注释）
    ├── embed_image: 图片推理（标注 ENGINEER SEAM 注释）
    └── embed_text: 文本推理（标注 ENGINEER SEAM 注释）
```

替换步骤：
1. 修改 `SiglipEmbedder.__init__` 中的模型加载逻辑
2. 修改 `embed_image` / `embed_text` 的推理逻辑
3. 确保输出仍为 **float32、L2 归一化、形状 `(embed_dim,)`**
4. 设置 `VISION_EMBED_DIM` 环境变量匹配新模型维度

### 替换融合算法 — `app/fusion.py`

```python
def fuse(image_sim, text_sim, process_sim, weights) -> float:
    # 当前: 线性加权求和
    # 可替换为: MLP re-ranker、LambdaMART 等
```

---

## API 文档

### `GET /health`

```json
{
  "ok": true,
  "mode": "mock",         // "mock" 或 "siglip"
  "indexed": 8,           // 索引中的样本数量
  "embed_dim": 768,
  "vector_store": "faiss"
}
```

### `POST /sample-search`

**请求体**（JSON）：

```json
{
  "image_base64": "<base64编码的图片>",   // 可选
  "image_url": "http://...",              // 可选（优先级低于 base64）
  "description": "提花织带 黑色",          // 可选，文字描述
  "filters": {
    "ribbon_type": "提花织带",            // 可选
    "width": "20mm",                      // 可选
    "tension": "soft"                     // 可选
  },
  "top_k": 5                              // 返回结果数，默认 10
}
```

**响应体**（JSON）：

```json
{
  "matches": [
    {
      "external_id": "ERP-10001",
      "sample_no": "HY-20-BK-soft",
      "score": 0.7832,
      "score_components": {
        "image": 0.9123,
        "text": 0.6541,
        "process": 1.0
      },
      "image_url": "/images/sample_001.png",
      "metadata": {
        "width": "20mm",
        "tension": "soft",
        "ribbon_type": "提花织带",
        "color": "黑色",
        "status": "queren"
      }
    }
  ]
}
```

**鉴权**（可选）：若设置 `VISION_SERVICE_TOKEN=<secret>`，请求需携带：
```
Authorization: Bearer <secret>
```

### `GET /images/{filename}`

返回语料库中的样本图片（StaticFiles 挂载）。

---

## 配置（环境变量）

| 变量名                     | 默认值                              | 说明                                  |
|--------------------------|-------------------------------------|---------------------------------------|
| `VISION_USE_MOCK`         | `true`                              | 是否使用 mock 嵌入器                   |
| `VISION_MODEL_PATH`       | `google/siglip-base-patch16-224`    | HF 模型 ID 或本地路径                  |
| `VISION_DEVICE`           | `auto`                              | `auto` / `mps` / `cuda` / `cpu`       |
| `VISION_EMBED_DIM`        | `768`                               | 嵌入向量维度                           |
| `VISION_VECTOR_STORE`     | `faiss`                             | 向量后端（目前仅支持 `faiss`）           |
| `VISION_INDEX_PATH`       | `./index`                           | 索引目录                               |
| `VISION_IMAGES_DIR`       | `./corpus`                          | 图片目录                               |
| `VISION_TOP_K_ANN`        | `50`                                | ANN 召回候选数                         |
| `VISION_FUSION_WEIGHTS`   | `{"image":0.5,"text":0.3,"process":0.2}` | 融合权重（JSON 字符串）           |
| `VISION_SERVICE_TOKEN`    | `null`                              | Bearer Token（空=不鉴权）              |

---

## 目录结构

```
vision-service/
├── app/
│   ├── __init__.py
│   ├── config.py          # 环境配置（pydantic-settings）
│   ├── model.py           # 嵌入器（Mock + SigLIP ENGINEER SEAM）
│   ├── vector_store.py    # 向量存储（FAISS / Qdrant 桩）
│   ├── fusion.py          # 三路融合算法（ENGINEER SEAM）
│   ├── schemas.py         # Pydantic 请求/响应模型
│   ├── search.py          # 核心检索逻辑
│   └── main.py            # FastAPI 应用入口
├── index_samples.py       # 离线索引构建 CLI
├── make_demo_corpus.py    # 演示语料库生成
├── requirements.txt       # 轻量依赖（无 torch）
├── Dockerfile
├── MANIFEST_FORMAT.md     # CSV 格式规范
└── README.md              # 本文档
```
