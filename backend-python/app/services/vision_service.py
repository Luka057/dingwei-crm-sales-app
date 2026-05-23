"""Vision service client — AI 找板 调公司视觉服务(SigLIP2 + 向量索引)。
后端瘦代理:base64 转发查询图 → POST /sample-search → 透传增强。
"""
from __future__ import annotations

import base64
from typing import Any

import httpx

from app.core.config import get_settings


class VisionServiceError(Exception):
    """视觉服务不可用/超时/出错,调用方转 503。"""


async def search_samples(
    image_bytes: bytes | None,
    description: str,
    filters: dict[str, str | None],
    top_k: int | None = None,
) -> list[dict[str, Any]]:
    """调视觉服务 /sample-search,返回 matches(已把 image_url 改写成 /vision-images/ 同源路径)。"""
    settings = get_settings()

    # 组装请求体
    payload: dict[str, Any] = {
        "description": description,
        "filters": {k: v for k, v in filters.items()},
        "top_k": top_k or settings.vision_top_k,
    }

    # 有图片时 base64 编码(不带 data: 前缀)
    if image_bytes:
        payload["image_base64"] = base64.b64encode(image_bytes).decode("ascii")

    # 可选 bearer token
    headers: dict[str, str] = {}
    if settings.vision_service_token is not None:
        headers["Authorization"] = f"Bearer {settings.vision_service_token.get_secret_value()}"

    url = settings.vision_service_url.rstrip("/") + "/sample-search"

    try:
        async with httpx.AsyncClient(timeout=settings.vision_timeout_seconds) as client:
            resp = await client.post(url, json=payload, headers=headers)
    except (httpx.TimeoutException, httpx.ConnectError, httpx.HTTPError) as exc:
        raise VisionServiceError(f"vision service unreachable: {exc}") from exc

    if resp.status_code != 200:
        raise VisionServiceError(
            f"vision service returned {resp.status_code}: {resp.text[:200]}"
        )

    try:
        body = resp.json()
    except ValueError as exc:  # 非 JSON 响应(如被反代注入 HTML 错误页)→ 当作服务异常
        raise VisionServiceError(
            f"vision service returned non-JSON: {resp.text[:200]}"
        ) from exc
    matches = body.get("matches", [])

    # 把 /images/x 改写成 /vision-images/x(前端经 nginx 同源反代)
    for m in matches:
        iu = m.get("image_url")
        if iu and iu.startswith("/images/"):
            m["image_url"] = "/vision-images/" + iu[len("/images/"):]

    return matches
