"""
Weekly Report service.

状态机(§3.5.6 / §4.5):
  draft → submitted(submit 无审批)→ reopened(manager 退回)→ submitted
  reopened 后 draft → submitted 再走一次。

权限(§3.5.2 + §3.5.3):
- GET /weekly-reports      WHERE salesperson_id = current_user.id
- GET /weekly-reports/{id} owner OR (manager 且 status IN submitted/reopened
                           且 sales.manager_id == current)
- POST                     默认 status=draft,UQ_weekly_owner_week
- PUT                      仅 draft / reopened
- POST submit              draft|reopened → submitted
- POST reopen              **manager-only** + 下属校验 + submitted → reopened
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.weekly_report import WeeklyReport, WeeklyReportStatus
from app.schemas.weekly_report import (
    WeeklyReportCreate,
    WeeklyReportOut,
    WeeklyReportUpdate,
)

if TYPE_CHECKING:
    from app.core.deps import AuthUser


class WeeklyReportError(Exception):
    def __init__(self, code: int, msg: str) -> None:
        super().__init__(msg)
        self.code = code
        self.msg = msg


def _iso_monday(d: date | None = None) -> date:
    """返回 d 所在 ISO 周的周一(d 默认 today)。"""
    d = d or date.today()
    return d - timedelta(days=d.weekday())


async def _to_out(db: AsyncSession, r: WeeklyReport) -> WeeklyReportOut:
    salesperson_name = await db.scalar(
        select(User.name).where(User.id == r.salesperson_id)
    )
    return WeeklyReportOut(
        id=r.id,
        salesperson_id=r.salesperson_id,
        salesperson_name=salesperson_name,
        week_start=r.week_start,
        summary=r.summary,
        next_plan=r.next_plan,
        notes=r.notes,
        attachments=r.attachments,
        status=r.status,
        created_at=r.created_at,
        updated_at=r.updated_at,
    )


# ── List ────────────────────────────────────────────────────────


async def list_my_reports(
    db: AsyncSession,
    user: "AuthUser",
) -> list[WeeklyReportOut]:
    """自己的周报(按 week_start 倒序)。"""
    stmt = (
        select(WeeklyReport)
        .where(WeeklyReport.salesperson_id == UUID(user.id))
        .order_by(WeeklyReport.week_start.desc())
    )
    reports = (await db.execute(stmt)).scalars().all()
    return [await _to_out(db, r) for r in reports]


# ── Get one ─────────────────────────────────────────────────────


async def get_report(
    db: AsyncSession,
    user: "AuthUser",
    report_id: UUID,
) -> WeeklyReportOut | None:
    """详情 — owner 或 manager 看下属的 submitted/reopened。"""
    report = (
        await db.execute(select(WeeklyReport).where(WeeklyReport.id == report_id))
    ).scalar_one_or_none()
    if report is None:
        return None

    current_id = UUID(user.id)

    if report.salesperson_id == current_id:
        return await _to_out(db, report)

    # 不是 owner → 看是不是 manager 看下属
    if not user.is_manager:
        return None

    if report.status not in (WeeklyReportStatus.SUBMITTED, WeeklyReportStatus.REOPENED):
        return None  # draft 不让主管看

    sales_manager_id = await db.scalar(
        select(User.manager_id).where(User.id == report.salesperson_id)
    )
    if sales_manager_id != current_id:
        return None

    return await _to_out(db, report)


# ── Create ──────────────────────────────────────────────────────


async def create_report(
    db: AsyncSession,
    user: "AuthUser",
    payload: WeeklyReportCreate,
) -> WeeklyReportOut:
    """default status=draft。week_start 未传时算本周 ISO 周一。"""
    week_start = payload.week_start or _iso_monday()
    report = WeeklyReport(
        salesperson_id=UUID(user.id),
        week_start=week_start,
        summary=payload.summary,
        next_plan=payload.next_plan,
        notes=payload.notes,
        attachments=payload.attachments,
        status=WeeklyReportStatus.DRAFT,
    )
    db.add(report)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise WeeklyReportError(
            409,
            f"weekly report for week {week_start.isoformat()} already exists",
        ) from exc
    await db.refresh(report)
    return await _to_out(db, report)


# ── Update ──────────────────────────────────────────────────────


async def update_report(
    db: AsyncSession,
    user: "AuthUser",
    report_id: UUID,
    payload: WeeklyReportUpdate,
) -> WeeklyReportOut | None:
    """仅 draft / reopened 状态可编。"""
    report = (
        await db.execute(
            select(WeeklyReport).where(
                WeeklyReport.id == report_id,
                WeeklyReport.salesperson_id == UUID(user.id),
            )
        )
    ).scalar_one_or_none()
    if report is None:
        return None

    if report.status not in (WeeklyReportStatus.DRAFT, WeeklyReportStatus.REOPENED):
        raise WeeklyReportError(
            409,
            f"cannot edit report in status={report.status.value} (only draft/reopened)",
        )

    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(report, key, value)
    await db.commit()
    await db.refresh(report)
    return await _to_out(db, report)


# ── Submit ──────────────────────────────────────────────────────


async def submit_report(
    db: AsyncSession,
    user: "AuthUser",
    report_id: UUID,
) -> WeeklyReportOut | None:
    """draft|reopened → submitted。无审批,提交即生效(§3.5.6)。"""
    report = (
        await db.execute(
            select(WeeklyReport).where(
                WeeklyReport.id == report_id,
                WeeklyReport.salesperson_id == UUID(user.id),
            )
        )
    ).scalar_one_or_none()
    if report is None:
        return None
    if report.status not in (WeeklyReportStatus.DRAFT, WeeklyReportStatus.REOPENED):
        raise WeeklyReportError(
            409,
            f"cannot submit report in status={report.status.value}",
        )
    report.status = WeeklyReportStatus.SUBMITTED
    await db.commit()
    await db.refresh(report)
    return await _to_out(db, report)


# ── Reopen(manager-only) ──────────────────────────────────────


async def reopen_report(
    db: AsyncSession,
    manager: "AuthUser",
    report_id: UUID,
) -> WeeklyReportOut | None:
    """submitted → reopened(让销售补充,非拒绝)。

    校验:
    - manager 角色(router 层 ManagerUser 已校验)
    - 该 report 的 salesperson 的 manager_id == current_manager.id
    - 状态必须是 submitted
    """
    report = (
        await db.execute(select(WeeklyReport).where(WeeklyReport.id == report_id))
    ).scalar_one_or_none()
    if report is None:
        return None

    sales_manager_id = await db.scalar(
        select(User.manager_id).where(User.id == report.salesperson_id)
    )
    if sales_manager_id != UUID(manager.id):
        return None  # 不是自己下属

    if report.status != WeeklyReportStatus.SUBMITTED:
        raise WeeklyReportError(
            409,
            f"can only reopen submitted reports (current={report.status.value})",
        )

    report.status = WeeklyReportStatus.REOPENED
    await db.commit()
    await db.refresh(report)
    return await _to_out(db, report)
