"""initial schema — 8 tables (Phase 1A baseline)

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-21

参考:
- docs/需求文档-v2.md §3.5 角色矩阵 + §5 数据契约
- plan/sorted-watching-lantern.md §1A.2 schema 设计
- docs/数据字典.md 字段对齐

SQL Server 注意:
- 外键 SetNull 仅用于 Plan.customer_id(避免多路 cascade 报错)
- ENUM 用 VARCHAR + CHECK 约束
- 时间用 DATETIME2 + sysutcdatetime()
- 主键 UNIQUEIDENTIFIER
- 过滤索引 mssql_where=...
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ══════════════════════════════════════════════════════════════
    # 1. user
    # ══════════════════════════════════════════════════════════════
    op.create_table(
        "user",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("username", sa.Unicode(64), nullable=False, unique=True),
        sa.Column("password_hash", sa.Unicode(255), nullable=False),
        sa.Column("name", sa.Unicode(64), nullable=False),
        sa.Column("role", sa.Unicode(16), nullable=False),
        sa.Column(
            "status",
            sa.Unicode(16),
            nullable=False,
            server_default=sa.text("'active'"),
        ),
        sa.Column(
            "manager_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("user.id", ondelete="NO ACTION", name="FK_user_manager"),
            nullable=True,
        ),
        # 集成预留
        sa.Column("external_id", sa.Unicode(64), nullable=True),
        sa.Column("source_system", sa.Unicode(32), nullable=True),
        sa.Column("synced_at", sa.DateTime(), nullable=True),
        # 时间戳
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.sysutcdatetime(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.sysutcdatetime(),
        ),
        sa.CheckConstraint(
            "role IN ('sales', 'manager', 'boss')", name="CK_user_role"
        ),
        sa.CheckConstraint(
            "status IN ('active', 'disabled', 'resigned')",
            name="CK_user_status",
        ),
    )
    op.create_index(
        "IX_user_external",
        "user",
        ["external_id"],
        mssql_where=sa.text("external_id IS NOT NULL"),
    )
    op.create_index("IX_user_manager", "user", ["manager_id"])

    # ══════════════════════════════════════════════════════════════
    # 2. customer
    # ══════════════════════════════════════════════════════════════
    op.create_table(
        "customer",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("name", sa.Unicode(128), nullable=False),
        sa.Column("short_name", sa.Unicode(64), nullable=True),
        sa.Column("contact_name", sa.Unicode(64), nullable=True),
        sa.Column("contact_title", sa.Unicode(64), nullable=True),
        sa.Column("phone", sa.Unicode(32), nullable=True),
        sa.Column("address", sa.Unicode(255), nullable=True),
        sa.Column(
            "level",
            sa.Unicode(4),
            nullable=False,
            server_default=sa.text("'B'"),
        ),
        sa.Column("ai_score", sa.Numeric(5, 2), nullable=True),
        sa.Column(
            "status",
            sa.Unicode(16),
            nullable=False,
            server_default=sa.text("'active'"),
        ),
        sa.Column(
            "owner_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("user.id", ondelete="NO ACTION", name="FK_customer_owner"),
            nullable=False,
        ),
        sa.Column("last_visit_at", sa.DateTime(), nullable=True),
        # 集成预留
        sa.Column("external_id", sa.Unicode(64), nullable=True),
        sa.Column("source_system", sa.Unicode(32), nullable=True),
        sa.Column("synced_at", sa.DateTime(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.sysutcdatetime(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.sysutcdatetime(),
        ),
        sa.CheckConstraint("level IN ('A', 'B', 'C')", name="CK_customer_level"),
        sa.CheckConstraint(
            "status IN ('active', 'inactive')",
            name="CK_customer_status",
        ),
    )
    op.create_index("IX_customer_owner", "customer", ["owner_id"])
    op.create_index(
        "IX_customer_owner_level", "customer", ["owner_id", "level"]
    )
    op.create_index(
        "IX_customer_owner_lastvisit",
        "customer",
        ["owner_id", "last_visit_at"],
    )
    op.create_index(
        "IX_customer_external",
        "customer",
        ["external_id"],
        mssql_where=sa.text("external_id IS NOT NULL"),
    )

    # ══════════════════════════════════════════════════════════════
    # 3. plan (唯一一处 SetNull:customer_id)
    # ══════════════════════════════════════════════════════════════
    op.create_table(
        "plan",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column(
            "salesperson_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey(
                "user.id",
                ondelete="NO ACTION",
                name="FK_plan_salesperson",
            ),
            nullable=False,
        ),
        sa.Column(
            "customer_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey(
                "customer.id",
                ondelete="SET NULL",  # 方案 1A.2 唯一 SetNull
                name="FK_plan_customer",
            ),
            nullable=True,
        ),
        sa.Column("title", sa.Unicode(128), nullable=False),
        sa.Column("type", sa.Unicode(16), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(), nullable=False),
        sa.Column("content", sa.UnicodeText(), nullable=True),
        sa.Column(
            "status",
            sa.Unicode(16),
            nullable=False,
            server_default=sa.text("'pending'"),
        ),
        sa.Column(
            "is_personal",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.sysutcdatetime(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.sysutcdatetime(),
        ),
        sa.CheckConstraint("type IN ('visit', 'custom')", name="CK_plan_type"),
        sa.CheckConstraint(
            "status IN ('pending', 'done', 'cancelled')",
            name="CK_plan_status",
        ),
    )
    op.create_index(
        "IX_plan_owner_scheduled",
        "plan",
        ["salesperson_id", "scheduled_at"],
    )
    op.create_index(
        "IX_plan_owner_personal",
        "plan",
        ["salesperson_id", "is_personal"],
    )

    # ══════════════════════════════════════════════════════════════
    # 4. visit_record
    # ══════════════════════════════════════════════════════════════
    op.create_table(
        "visit_record",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column(
            "customer_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey(
                "customer.id",
                ondelete="NO ACTION",
                name="FK_visit_customer",
            ),
            nullable=False,
        ),
        sa.Column(
            "salesperson_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey(
                "user.id",
                ondelete="NO ACTION",
                name="FK_visit_salesperson",
            ),
            nullable=False,
        ),
        sa.Column("visit_at", sa.DateTime(), nullable=False),
        sa.Column("method", sa.Unicode(16), nullable=False),
        sa.Column(
            "intention",
            sa.Unicode(16),
            nullable=False,
            server_default=sa.text("'none'"),
        ),
        sa.Column("target_person", sa.Unicode(64), nullable=True),
        sa.Column("target_title", sa.Unicode(64), nullable=True),
        sa.Column("content", sa.UnicodeText(), nullable=True),
        sa.Column("ai_summary", sa.UnicodeText(), nullable=True),
        sa.Column("next_follow_at", sa.DateTime(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.sysutcdatetime(),
        ),
        sa.CheckConstraint(
            "method IN ('offline', 'phone', 'wechat')",
            name="CK_visit_method",
        ),
        sa.CheckConstraint(
            "intention IN ('good', 'likely_order', 'wait', 'none')",
            name="CK_visit_intention",
        ),
    )
    op.create_index(
        "IX_visit_owner_visitat",
        "visit_record",
        ["salesperson_id", "visit_at"],
    )
    op.create_index(
        "IX_visit_customer_visitat",
        "visit_record",
        ["customer_id", "visit_at"],
    )

    # ══════════════════════════════════════════════════════════════
    # 5. visit_attachment
    # ══════════════════════════════════════════════════════════════
    op.create_table(
        "visit_attachment",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        # 1A:nullable 允许"先上传后绑定 visit"(orphan attachment 由 1B GC 清理)
        sa.Column(
            "visit_record_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey(
                "visit_record.id",
                ondelete="CASCADE",  # 拜访记录删除时级联清照片
                name="FK_attachment_visit",
            ),
            nullable=True,
        ),
        # uploader_id:权限校验 + 限速依据,NOT NULL
        sa.Column(
            "uploader_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey(
                "user.id",
                ondelete="NO ACTION",
                name="FK_attachment_uploader",
            ),
            nullable=False,
        ),
        sa.Column(
            "type",
            sa.Unicode(16),
            nullable=False,
            server_default=sa.text("'photo'"),
        ),
        sa.Column("storage_path", sa.Unicode(255), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("mime_type", sa.Unicode(32), nullable=False),
        sa.Column(
            "uploaded_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.sysutcdatetime(),
        ),
        sa.CheckConstraint("type IN ('photo')", name="CK_attachment_type"),
    )
    op.create_index(
        "IX_visit_attachment_visit",
        "visit_attachment",
        ["visit_record_id"],
    )
    op.create_index(
        "IX_visit_attachment_uploader_uploaded",
        "visit_attachment",
        ["uploader_id", "uploaded_at"],
    )

    # ══════════════════════════════════════════════════════════════
    # 6. weekly_report
    # ══════════════════════════════════════════════════════════════
    op.create_table(
        "weekly_report",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column(
            "salesperson_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey(
                "user.id",
                ondelete="NO ACTION",
                name="FK_weekly_salesperson",
            ),
            nullable=False,
        ),
        sa.Column("week_start", sa.Date(), nullable=False),
        sa.Column("summary", sa.UnicodeText(), nullable=True),
        sa.Column("next_plan", sa.UnicodeText(), nullable=True),
        sa.Column("notes", sa.UnicodeText(), nullable=True),
        sa.Column("attachments", sa.JSON(), nullable=True),
        sa.Column(
            "status",
            sa.Unicode(16),
            nullable=False,
            server_default=sa.text("'draft'"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.sysutcdatetime(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.sysutcdatetime(),
        ),
        sa.UniqueConstraint(
            "salesperson_id", "week_start", name="UQ_weekly_owner_week"
        ),
        sa.CheckConstraint(
            "status IN ('draft', 'submitted', 'reopened')",
            name="CK_weekly_status",
        ),
    )
    op.create_index(
        "IX_weekly_owner_status", "weekly_report", ["salesperson_id", "status"]
    )

    # ══════════════════════════════════════════════════════════════
    # 7. sample (1A 建表不开 router)
    # ══════════════════════════════════════════════════════════════
    op.create_table(
        "sample",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column(
            "customer_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey(
                "customer.id",
                ondelete="NO ACTION",
                name="FK_sample_customer",
            ),
            nullable=False,
        ),
        sa.Column(
            "salesperson_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey(
                "user.id",
                ondelete="NO ACTION",
                name="FK_sample_salesperson",
            ),
            nullable=False,
        ),
        sa.Column("sample_no", sa.Unicode(64), nullable=False),
        sa.Column(
            "status",
            sa.Unicode(32),
            nullable=False,
            server_default=sa.text("'qiyang'"),
        ),
        sa.Column("width", sa.Unicode(32), nullable=True),
        sa.Column("tension", sa.Unicode(32), nullable=True),
        sa.Column("ribbon_type", sa.Unicode(32), nullable=True),
        sa.Column("color", sa.Unicode(64), nullable=True),
        sa.Column("image_url", sa.Unicode(255), nullable=True),
        sa.Column("notes", sa.UnicodeText(), nullable=True),
        sa.Column("external_id", sa.Unicode(64), nullable=True),
        sa.Column("source_system", sa.Unicode(32), nullable=True),
        sa.Column("synced_at", sa.DateTime(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.sysutcdatetime(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.sysutcdatetime(),
        ),
        sa.CheckConstraint(
            "status IN ('qiyang', 'zhongban', 'queren', 'yizhuandingdan', 'yifangqi')",
            name="CK_sample_status",
        ),
    )
    op.create_index("IX_sample_customer", "sample", ["customer_id"])
    op.create_index(
        "IX_sample_external",
        "sample",
        ["external_id"],
        mssql_where=sa.text("external_id IS NOT NULL"),
    )

    # ══════════════════════════════════════════════════════════════
    # 8. customer_transfer
    # ══════════════════════════════════════════════════════════════
    op.create_table(
        "customer_transfer",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column(
            "customer_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey(
                "customer.id",
                ondelete="NO ACTION",
                name="FK_transfer_customer",
            ),
            nullable=False,
        ),
        sa.Column(
            "from_user_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey(
                "user.id",
                ondelete="NO ACTION",
                name="FK_transfer_from_user",
            ),
            nullable=False,
        ),
        sa.Column(
            "to_user_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey(
                "user.id",
                ondelete="NO ACTION",
                name="FK_transfer_to_user",
            ),
            nullable=False,
        ),
        sa.Column(
            "initiated_by_user_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey(
                "user.id",
                ondelete="NO ACTION",
                name="FK_transfer_initiated_by",
            ),
            nullable=False,
        ),
        sa.Column("flow", sa.Unicode(32), nullable=False),
        sa.Column(
            "status",
            sa.Unicode(16),
            nullable=False,
            server_default=sa.text("'pending'"),
        ),
        sa.Column("reason", sa.Unicode(500), nullable=True),
        sa.Column(
            "requested_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.sysutcdatetime(),
        ),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column(
            "reviewed_by_user_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey(
                "user.id",
                ondelete="NO ACTION",
                name="FK_transfer_reviewed_by",
            ),
            nullable=True,
        ),
        sa.CheckConstraint(
            "flow IN ('manager_direct', 'sales_request')",
            name="CK_transfer_flow",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'approved', 'rejected', 'executed')",
            name="CK_transfer_status",
        ),
    )
    op.create_index(
        "IX_transfer_status",
        "customer_transfer",
        ["status", "requested_at"],
    )
    op.create_index(
        "IX_transfer_from_user", "customer_transfer", ["from_user_id"]
    )
    op.create_index(
        "IX_transfer_to_user", "customer_transfer", ["to_user_id"]
    )
    op.create_index(
        "IX_transfer_customer", "customer_transfer", ["customer_id"]
    )


def downgrade() -> None:
    """完整回滚 — 按 FK 反向顺序删表。"""
    op.drop_table("customer_transfer")
    op.drop_table("sample")
    op.drop_table("weekly_report")
    op.drop_table("visit_attachment")
    op.drop_table("visit_record")
    op.drop_table("plan")
    op.drop_table("customer")
    op.drop_table("user")
