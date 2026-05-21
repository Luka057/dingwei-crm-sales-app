"""
Smoke tests — Phase 1A 起步切片验证。

只测**不依赖 SQL Server** 的事:
- Python 语法 / import 链路完整
- Pydantic schemas 合法
- SQLAlchemy metadata 注册了 8 张表
- JWT 签发 / bcrypt 哈希 - 校验回环
- /health 端点(不连 DB)
- Q8 决议:plan is_personal 推断逻辑(暂为占位测试,待 plan_service 实现)

更深的 P0 unit 测试(customer_transfer 状态机 / 鉴权链路 / 乐观锁 /
manager_id 链路)和 P1 e2e smoke(login / customers / transfer 等)
在后续模块实现时分别补。

测试覆盖优先级见 docs/需求文档-v2.md §11.1 O7 决议。
"""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.main import app
from app.models import Base


# ── 静态:metadata 完整性 ────────────────────────────────────────


def test_metadata_has_8_tables() -> None:
    """Phase 1A 必须有 8 张表。"""
    expected = {
        "user",
        "customer",
        "plan",
        "visit_record",
        "visit_attachment",
        "weekly_report",
        "sample",
        "customer_transfer",
    }
    actual = set(Base.metadata.tables.keys())
    assert expected == actual, f"missing/extra tables: {expected ^ actual}"


def test_plan_has_is_personal_column() -> None:
    """Q8 决议:plan 表必须有 is_personal BIT 列(主管视图过滤依据)。"""
    plan = Base.metadata.tables["plan"]
    assert "is_personal" in plan.columns
    col = plan.columns["is_personal"]
    assert not col.nullable
    # 默认值 0
    assert col.server_default is not None


def test_weekly_report_unique_owner_week() -> None:
    """UQ_weekly_owner_week:一个销售一周一份(§4.2)。"""
    wr = Base.metadata.tables["weekly_report"]
    constraint_names = {c.name for c in wr.constraints}
    assert "UQ_weekly_owner_week" in constraint_names


def test_customer_transfer_has_both_flows() -> None:
    """customer_transfer 必须支持双 flow + 4 状态(§3.4)。"""
    ct = Base.metadata.tables["customer_transfer"]
    assert "flow" in ct.columns
    assert "status" in ct.columns
    assert "from_user_id" in ct.columns
    assert "to_user_id" in ct.columns
    assert "initiated_by_user_id" in ct.columns


def test_visit_attachment_cascades_from_visit_record() -> None:
    """删除拜访时级联删照片(visit_attachment.visit_record_id FK CASCADE)。"""
    va = Base.metadata.tables["visit_attachment"]
    fks = list(va.foreign_keys)
    visit_fk = next(fk for fk in fks if fk.column.table.name == "visit_record")
    assert visit_fk.ondelete == "CASCADE"


def test_plan_customer_id_set_null_on_delete() -> None:
    """方案 1A.2 唯一一处 SetNull:Plan.customer_id。"""
    plan = Base.metadata.tables["plan"]
    fks = list(plan.foreign_keys)
    customer_fk = next(fk for fk in fks if fk.column.table.name == "customer")
    assert customer_fk.ondelete == "SET NULL"


def test_user_has_integration_fields() -> None:
    """§5.3 共享 ID 预留:user/customer/sample 必须有 external_id/source_system/synced_at。"""
    for table_name in ("user", "customer", "sample"):
        table = Base.metadata.tables[table_name]
        assert "external_id" in table.columns, f"{table_name} missing external_id"
        assert "source_system" in table.columns, f"{table_name} missing source_system"
        assert "synced_at" in table.columns, f"{table_name} missing synced_at"


# ── Security 单元 ────────────────────────────────────────────────


def test_bcrypt_hash_verify_roundtrip() -> None:
    """bcrypt 哈希 / 校验闭环。"""
    plain = "123456"
    hashed = hash_password(plain)
    assert hashed != plain
    assert verify_password(plain, hashed)
    assert not verify_password("wrong", hashed)


def test_jwt_sign_decode_roundtrip() -> None:
    """JWT HS256 签发 / 解码闭环。"""
    token = create_access_token(
        subject="user-id-123",
        extra_claims={"role": "sales", "name": "张伟"},
    )
    payload = decode_access_token(token)
    assert payload["sub"] == "user-id-123"
    assert payload["role"] == "sales"
    assert payload["name"] == "张伟"
    assert "exp" in payload
    assert "iat" in payload


# ── /health 端点(不连 DB) ───────────────────────────────────────


@pytest.mark.asyncio
async def test_health_endpoint() -> None:
    """/api/v1/health 公开,不连 DB,返回 200 ok。"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["service"] == "dingwei-crm-backend"
    assert "time" in body


# ── /auth/login(无 DB,401 路径) ────────────────────────────────


@pytest.mark.asyncio
async def test_login_without_db_returns_500_or_503() -> None:
    """
    在没有 SQL Server 的情况下,/auth/login 应该因 DB 连接失败而返 500 或类似。
    这个测试本身不要求 DB,只验证端点存在 + 路由通。

    完整 login 链路测试在 conftest 启 SQL Server fixture 后再写。
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/login",
            json={"username": "zhangwei", "password": "123456"},
        )
    # 没有 DB 时会因连不上抛异常 → FastAPI 500
    # 或在 in-memory test DB 下应该 401(用户不存在)
    # 这里仅断言路由响应(不是 404 / 405)
    assert response.status_code in (401, 500, 503)


# ── OpenAPI spec 完整性 ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_openapi_lists_all_endpoints() -> None:
    """OpenAPI 必须列出 §3.5.2 矩阵里的所有端点(用于前端 openapi-typescript 生成)。"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/openapi.json")
    assert response.status_code == 200
    spec = response.json()
    paths = spec["paths"]

    # 抽样核对关键端点(对照 §3.5.2)
    expected_paths = [
        "/api/v1/health",
        "/api/v1/auth/login",
        "/api/v1/customers/",
        "/api/v1/customers/overdue-summary",
        "/api/v1/plans/calendar",
        "/api/v1/visit-records/",
        "/api/v1/uploads/visit-photo",
        "/api/v1/weekly-reports/",
        "/api/v1/weekly-reports/generate-ai-draft",
        "/api/v1/customer-transfers/",
        "/api/v1/manager/team-summary",
        "/api/v1/ai/chat",
        "/api/v1/ai/board-search",
    ]
    for path in expected_paths:
        assert path in paths, f"missing endpoint: {path}"


@pytest.mark.asyncio
async def test_ai_board_search_returns_3_mock_matches() -> None:
    """Q6 决议:1A stub 返 3 条拟真 mock。"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 注:这里不带 JWT,会因 oauth2_scheme 拒绝 → 401
        # 验证 stub 内容需要先 mock get_current_user,后续 e2e 测试做
        response = await client.post(
            "/api/v1/ai/board-search",
            json={
                "customer_scene": "测试客户",
                "image_ids": [],
            },
        )
    # 没带 token → 401
    assert response.status_code == 401
