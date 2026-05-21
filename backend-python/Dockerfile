# 鼎伟 CRM 业务人员端 - Python backend Dockerfile
#
# 关键决策:
# - python:3.11-slim 作为基础(stretch 太老,bullseye/bookworm 兼容 ODBC 18)
# - Microsoft ODBC Driver 18 是 SQLAlchemy + aioodbc 跑 SQL Server 的依赖
# - mssql-tools18 提供 sqlcmd,docker-compose entrypoint 用来 IF DB_ID create
# - python-magic 需要系统 libmagic1
#
# 1A 注意:本 Dockerfile 未做多阶段构建 + 非 root 强化,
# 这些放在 Phase 1A.10 不做清单(生产 Dockerfile 强化)。
# Phase 2 / 试点扩量前必须做。

FROM python:3.11-slim-bookworm

# ── 系统依赖 ────────────────────────────────────────────────────
# 1. curl/gnupg/apt-utils 用于 添加 Microsoft 仓库
# 2. unixodbc-dev 是 pyodbc 的编译依赖
# 3. libmagic1 是 python-magic 的运行时依赖(magic bytes 校验)
# 4. build-essential 给某些纯 Python 包提供 C 编译能力
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        gnupg \
        ca-certificates \
        apt-transport-https \
        build-essential \
        unixodbc-dev \
        libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# ── Microsoft ODBC Driver 18 + mssql-tools18 ───────────────────
# 官方安装步骤:https://learn.microsoft.com/sql/connect/odbc/linux-mac/installing-the-microsoft-odbc-driver-for-sql-server
RUN curl -fsSL https://packages.microsoft.com/keys/microsoft.asc \
        | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
    && echo "deb [arch=amd64,arm64 signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" \
        > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y --no-install-recommends \
        msodbcsql18 \
        mssql-tools18 \
    && rm -rf /var/lib/apt/lists/*

# 让 sqlcmd 在 PATH
ENV PATH="/opt/mssql-tools18/bin:${PATH}"

# ── Python 依赖 ────────────────────────────────────────────────
WORKDIR /app

# 先拷依赖配置,利用 Docker 缓存层
COPY pyproject.toml ./

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -e .

# ── 应用源码 ────────────────────────────────────────────────────
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini ./

# uploads 目录由 docker volume 挂载
RUN mkdir -p /app/uploads/visits

# ── 启动 ────────────────────────────────────────────────────────
EXPOSE 3000

# 默认 command 在 docker-compose 里覆盖(跑 alembic + seed + uvicorn)
# 单独 docker run 时直接 uvicorn,需要先手动 alembic
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "3000"]
