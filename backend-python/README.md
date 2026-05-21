# dingwei-crm-backend (Phase 1A)

鼎伟 CRM 业务人员端 — Python 后端。

> **权威需求文档**:`../docs/需求文档-v2.md`(v2.1 整合版)
> **方案文件**:`/Users/jasper/Desktop/鼎伟crm（自建）/plan/sorted-watching-lantern.md`
> **角色矩阵**:`需求文档-v2.md §3.5` + 附录 C 速查表

## Phase 1A 范围

- 9 个业务模块,**23 个真实端点 + 3 stub**(详见 `需求文档-v2.md §3.5.2`)
- SQL Server 2022 + SQLAlchemy 2.x async + Alembic
- JWT 鉴权,bcrypt 密码
- AI 端点全 stub(Phase 1B 接 DeepSeek)

## 技术栈

| 层 | 选型 |
|---|---|
| 语言 | Python 3.11+ |
| 框架 | FastAPI |
| ORM | SQLAlchemy 2.x (async) |
| 迁移 | Alembic |
| DB | SQL Server 2022 + aioodbc + Microsoft ODBC Driver 18 |
| 鉴权 | JWT (python-jose) + bcrypt (passlib) |
| 配置 | pydantic-settings |
| 测试 | pytest + pytest-asyncio + httpx |

## 目录结构

```
backend-python/
├── pyproject.toml
├── alembic.ini
├── alembic/
│   ├── env.py
│   └── versions/
├── app/
│   ├── main.py                # FastAPI 入口
│   ├── core/
│   │   ├── config.py          # pydantic-settings
│   │   ├── security.py        # JWT + bcrypt
│   │   └── deps.py            # get_current_user / require_manager
│   ├── db/
│   │   ├── base.py            # AsyncEngine
│   │   ├── session.py         # async_sessionmaker
│   │   └── seed.py            # 种子脚本
│   ├── models/                # SQLAlchemy ORM
│   ├── schemas/               # Pydantic v2 DTO
│   ├── services/              # 业务逻辑层(每方法首参 user: AuthUser)
│   └── api/v1/                # FastAPI router
├── tests/
└── uploads/visits/            # docker volume(本地)
```

## 启动方式

### Docker(首选)

```bash
cd /Users/jasper/Desktop/鼎伟crm（自建）/dingwei-crm-sales-app--phase-1a-backend
docker compose up -d sqlserver         # 等 healthy(首次拉镜像 30-60s)
docker compose up -d backend            # 自动跑 alembic + seed + uvicorn
curl http://localhost:3000/api/v1/health
```

### 本机直跑(Mac 调试用,需 ODBC driver)

```bash
# 一次性
brew tap microsoft/mssql-release
brew install msodbcsql18 mssql-tools18

# 装 Python 依赖
cd backend-python
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# 跑(需要 docker compose up sqlserver 先起)
alembic upgrade head
python -m app.db.seed --if-empty
uvicorn app.main:app --reload --port 3000
```

## 角色 × 端点矩阵(实施核对)

见 `../docs/需求文档-v2.md §3.5.2`。每个 router 文件顶部加注释引用对应行。

## 测试

```bash
pytest                  # 跑所有
pytest -m smoke         # 仅 smoke
pytest -m unit          # P0 unit(state machine / 鉴权链路 / 乐观锁 / is_personal)
pytest -m e2e           # P1 e2e
```

测试优先级见 `../docs/需求文档-v2.md §11.1` O7 决议。
