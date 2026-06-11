# ─────────────────────────────────────────────────────────────────
# vision-service Dockerfile
# 基础镜像: python:3.11-slim（约 150MB）
#
# 注意: Docker Desktop for Mac 的 Linux 容器没有 MPS（Apple Silicon GPU）；
#       容器内始终使用 CPU 推理（VISION_DEVICE=cpu 或 auto→cpu）。
#       如需 GPU 加速，请在 Linux 宿主机 + NVIDIA GPU 上运行，
#       并替换为 pytorch/pytorch:2.x-cuda12.x-... 基础镜像。
# ─────────────────────────────────────────────────────────────────

FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 先复制 requirements.txt，利用 Docker 层缓存
# （只要依赖不变，此层不会重新构建）
COPY requirements.txt .

# 安装 Python 依赖
# --no-cache-dir: 不保留 pip 缓存，减小镜像体积
# -q: 减少输出
RUN pip install --no-cache-dir -q -r requirements.txt

# 复制应用代码
COPY app/ ./app/
COPY index_samples.py .

# 暴露端口
EXPOSE 8000

# 健康检查（容器启动后每 30 秒检查一次）
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" \
  || exit 1

# 启动命令
# --host 0.0.0.0: 监听所有接口（容器内需要，否则宿主机无法访问）
# --port 8000: 与 EXPOSE 一致
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
