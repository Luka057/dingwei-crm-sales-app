"""
种子数据 — Phase 1A 试点用。

用法:
  python -m app.db.seed              # 强制清表 + 重建
  python -m app.db.seed --if-empty   # 仅当 user 表为空时执行(docker 启动幂等)

参考方案文件 1A.5:
- 3 sales(zhangwei / liuyang / chenmin)
- 1 manager(wangManager,作为 3 sales 的 manager_id)
- 1 boss(seed 留位,本应用不允许登录,Phase 2 回传测试用)
- 6 客户:zhangwei 3 / liuyang 2 / chenmin 1
- zhangwei 本周一到周五铺 6-8 plans + 上周 done 2
- 3 visit_records(zhangwei,1 条带 ai_summary)
- 1 上周 submitted weekly_report(zhangwei)
- 2 samples

密码全 `123456`(bcrypt.hash)。试点开始前 O4 决议需改强密码。
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.db.session import AsyncSessionLocal
from app.models import (
    Customer,
    CustomerLevel,
    Plan,
    PlanStatus,
    PlanType,
    Sample,
    SampleStatus,
    User,
    UserRole,
    UserStatus,
    VisitIntention,
    VisitMethod,
    VisitRecord,
    WeeklyReport,
    WeeklyReportStatus,
)


# 固定 UUID 便于跨次 seed / 测试断言
USER_IDS = {
    "wang_manager": UUID("11111111-1111-1111-1111-111111111111"),
    "zhang_wei": UUID("22222222-2222-2222-2222-222222222222"),
    "liu_yang": UUID("33333333-3333-3333-3333-333333333333"),
    "chen_min": UUID("44444444-4444-4444-4444-444444444444"),
    "boss": UUID("55555555-5555-5555-5555-555555555555"),
}

CUSTOMER_IDS = {
    "hongyuan": UUID("a0000001-0000-0000-0000-000000000001"),
    "jinhua": UUID("a0000002-0000-0000-0000-000000000002"),
    "hengjia": UUID("a0000003-0000-0000-0000-000000000003"),
    "dongchen": UUID("a0000004-0000-0000-0000-000000000004"),
    "haitai": UUID("a0000005-0000-0000-0000-000000000005"),
    "minghui": UUID("a0000006-0000-0000-0000-000000000006"),
}


def _week_monday(d: date | None = None) -> date:
    """返回 ISO 周一(d 默认 today)。"""
    d = d or date.today()
    return d - timedelta(days=d.weekday())


async def _is_empty(db: AsyncSession) -> bool:
    result = await db.execute(select(User).limit(1))
    return result.scalar_one_or_none() is None


async def _truncate(db: AsyncSession) -> None:
    """按 FK 反向顺序清表。"""
    # 子表 → 父表
    from app.models import CustomerTransfer, VisitAttachment

    for model in (
        VisitAttachment,
        CustomerTransfer,
        WeeklyReport,
        VisitRecord,
        Plan,
        Sample,
        Customer,
        User,
    ):
        await db.execute(delete(model))


async def _seed_users(db: AsyncSession) -> None:
    pw = hash_password("123456")

    db.add_all([
        # Manager
        User(
            id=USER_IDS["wang_manager"],
            username="wangManager",
            password_hash=pw,
            name="王主管",
            role=UserRole.MANAGER,
            status=UserStatus.ACTIVE,
            manager_id=None,
        ),
        # 3 Sales,manager_id = wangManager
        User(
            id=USER_IDS["zhang_wei"],
            username="zhangwei",
            password_hash=pw,
            name="张伟",
            role=UserRole.SALES,
            status=UserStatus.ACTIVE,
            manager_id=USER_IDS["wang_manager"],
        ),
        User(
            id=USER_IDS["liu_yang"],
            username="liuyang",
            password_hash=pw,
            name="刘洋",
            role=UserRole.SALES,
            status=UserStatus.ACTIVE,
            manager_id=USER_IDS["wang_manager"],
        ),
        User(
            id=USER_IDS["chen_min"],
            username="chenmin",
            password_hash=pw,
            name="陈敏",
            role=UserRole.SALES,
            status=UserStatus.ACTIVE,
            manager_id=USER_IDS["wang_manager"],
        ),
        # Boss(本应用不允许登录,保留供 Phase 2 回传测试)
        User(
            id=USER_IDS["boss"],
            username="boss",
            password_hash=pw,
            name="老板",
            role=UserRole.BOSS,
            status=UserStatus.ACTIVE,
            manager_id=None,
        ),
    ])
    await db.flush()


async def _seed_customers(db: AsyncSession) -> None:
    now = datetime.now(UTC).replace(tzinfo=None)
    # 用不同的 last_visit_at 模拟超期 / 本周拜访等场景
    db.add_all([
        # zhangwei 3 客户:1 超期 / 1 本周拜访 / 1 普通
        Customer(
            id=CUSTOMER_IDS["hongyuan"],
            name="宏远服饰",
            short_name="宏远",
            level=CustomerLevel.A,
            owner_id=USER_IDS["zhang_wei"],
            contact_name="李总",
            contact_title="总经理",
            phone="138****6271",
            address="佛山南海区里水镇宏远工业园",
            last_visit_at=now - timedelta(days=20),  # A 类 14 天 → 超期
        ),
        Customer(
            id=CUSTOMER_IDS["jinhua"],
            name="锦华辅料",
            short_name="锦华",
            level=CustomerLevel.A,
            owner_id=USER_IDS["zhang_wei"],
            contact_name="陈经理",
            contact_title="采购经理",
            phone="139****4118",
            address="广州番禺区石基镇锦华工业区",
            last_visit_at=now - timedelta(days=18),  # A 类 14 天 → 超期
        ),
        Customer(
            id=CUSTOMER_IDS["hengjia"],
            name="恒嘉箱包",
            short_name="恒嘉",
            level=CustomerLevel.B,
            owner_id=USER_IDS["zhang_wei"],
            contact_name="王小姐",
            contact_title="采购",
            phone="136****9082",
            address="东莞厚街镇恒嘉箱包园区",
            last_visit_at=now - timedelta(days=5),  # B 类 30 天 → 未超期
        ),
        # liuyang 2 客户
        Customer(
            id=CUSTOMER_IDS["dongchen"],
            name="东晨制衣",
            short_name="东晨",
            level=CustomerLevel.B,
            owner_id=USER_IDS["liu_yang"],
            contact_name="赵主管",
            phone="135****7728",
            address="中山西区东晨服装园",
            last_visit_at=now - timedelta(days=12),
        ),
        Customer(
            id=CUSTOMER_IDS["haitai"],
            name="海泰户外",
            short_name="海泰",
            level=CustomerLevel.C,
            owner_id=USER_IDS["liu_yang"],
            contact_name="周经理",
            phone="137****1129",
            address="深圳龙岗区海泰工业园",
            last_visit_at=now - timedelta(days=80),  # C 类 60 天 → 超期
            ai_score=Decimal("62.50"),  # 示例 ai_score 留位
        ),
        # chenmin 1 客户
        Customer(
            id=CUSTOMER_IDS["minghui"],
            name="明辉鞋业",
            short_name="明辉",
            level=CustomerLevel.B,
            owner_id=USER_IDS["chen_min"],
            contact_name="孙总",
            phone="133****4561",
            address="温州瓯海区明辉鞋业园",
            last_visit_at=None,  # 从未拜访
        ),
    ])
    await db.flush()


async def _seed_plans(db: AsyncSession) -> None:
    """zhangwei 本周一到周五 6-8 plans + 上周 done 2 + 1 个人提醒。"""
    today = date.today()
    monday = _week_monday(today)
    last_monday = monday - timedelta(days=7)
    salesperson = USER_IDS["zhang_wei"]

    plans = [
        # 上周 2 done
        Plan(
            id=uuid4(),
            salesperson_id=salesperson,
            customer_id=CUSTOMER_IDS["hongyuan"],
            title="宏远服饰回访",
            type=PlanType.VISIT,
            scheduled_at=datetime.combine(last_monday + timedelta(days=2), time(10, 0)),
            content="确认上次样板反馈",
            status=PlanStatus.DONE,
            is_personal=False,
        ),
        Plan(
            id=uuid4(),
            salesperson_id=salesperson,
            customer_id=CUSTOMER_IDS["jinhua"],
            title="锦华辅料新报价",
            type=PlanType.VISIT,
            scheduled_at=datetime.combine(last_monday + timedelta(days=4), time(14, 30)),
            content="带新报价拜访",
            status=PlanStatus.DONE,
            is_personal=False,
        ),
        # 本周 6 plans
        Plan(
            id=uuid4(),
            salesperson_id=salesperson,
            customer_id=CUSTOMER_IDS["hongyuan"],
            title="宏远服饰",
            type=PlanType.VISIT,
            scheduled_at=datetime.combine(monday, time(9, 30)),
            content="确认宽度调整样板反馈",
            status=PlanStatus.PENDING,
            is_personal=False,
        ),
        Plan(
            id=uuid4(),
            salesperson_id=salesperson,
            customer_id=CUSTOMER_IDS["jinhua"],
            title="锦华辅料",
            type=PlanType.VISIT,
            scheduled_at=datetime.combine(monday, time(14, 30)),
            content="带新报价线下拜访",
            status=PlanStatus.PENDING,
            is_personal=False,
        ),
        Plan(
            id=uuid4(),
            salesperson_id=salesperson,
            customer_id=CUSTOMER_IDS["hengjia"],
            title="恒嘉箱包样板进展",
            type=PlanType.VISIT,
            scheduled_at=datetime.combine(monday + timedelta(days=1), time(10, 0)),
            status=PlanStatus.PENDING,
            is_personal=False,
        ),
        Plan(
            id=uuid4(),
            salesperson_id=salesperson,
            customer_id=None,
            title="周中整理客户档案",
            type=PlanType.CUSTOM,
            scheduled_at=datetime.combine(monday + timedelta(days=2), time(16, 0)),
            content="工作准备:整理本周拜访资料",
            status=PlanStatus.PENDING,
            is_personal=False,  # 销售手动改为业务提醒
        ),
        Plan(
            id=uuid4(),
            salesperson_id=salesperson,
            customer_id=CUSTOMER_IDS["hongyuan"],
            title="宏远样板二次确认",
            type=PlanType.VISIT,
            scheduled_at=datetime.combine(monday + timedelta(days=3), time(15, 0)),
            status=PlanStatus.PENDING,
            is_personal=False,
        ),
        Plan(
            id=uuid4(),
            salesperson_id=salesperson,
            customer_id=None,
            title="下周报价初稿",
            type=PlanType.CUSTOM,
            scheduled_at=datetime.combine(monday + timedelta(days=4), time(17, 0)),
            content="工作准备:周五下班前完成",
            status=PlanStatus.PENDING,
            is_personal=False,
        ),
        # 个人提醒(Q8 后端推断默认 True,演示销售手动 toggle 后保留默认)
        Plan(
            id=uuid4(),
            salesperson_id=salesperson,
            customer_id=None,
            title="喝水提醒",
            type=PlanType.CUSTOM,
            scheduled_at=datetime.combine(today, time(10, 30)),
            content="每天 10:30 提醒",
            status=PlanStatus.PENDING,
            is_personal=True,
        ),
    ]
    db.add_all(plans)
    await db.flush()


async def _seed_visit_records(db: AsyncSession) -> None:
    """zhangwei 近 2 周 3 条,其中 1 条带 ai_summary。"""
    now = datetime.now(UTC).replace(tzinfo=None)
    salesperson = USER_IDS["zhang_wei"]

    db.add_all([
        VisitRecord(
            id=uuid4(),
            customer_id=CUSTOMER_IDS["hongyuan"],
            salesperson_id=salesperson,
            visit_at=now - timedelta(days=20),
            method=VisitMethod.PHONE,
            intention=VisitIntention.LIKELY_ORDER,
            target_person="李总",
            target_title="总经理",
            content=(
                "客户认可上次织带手感,但担心颜色批次稳定性。"
                "本周需重新确认宽度,月底有试单机会。"
            ),
            ai_summary=(
                "客户认可手感,主要顾虑颜色批次稳定性;"
                "本周需重新确认宽度,月底有试单机会。"
            ),
        ),
        VisitRecord(
            id=uuid4(),
            customer_id=CUSTOMER_IDS["jinhua"],
            salesperson_id=salesperson,
            visit_at=now - timedelta(days=18),
            method=VisitMethod.OFFLINE,
            intention=VisitIntention.WAIT,
            target_person="陈经理",
            content="新报价已发送,等客户内部讨论。",
        ),
        VisitRecord(
            id=uuid4(),
            customer_id=CUSTOMER_IDS["hengjia"],
            salesperson_id=salesperson,
            visit_at=now - timedelta(days=5),
            method=VisitMethod.WECHAT,
            intention=VisitIntention.GOOD,
            target_person="王小姐",
            content="样板已确认,等待下订单。",
        ),
    ])
    await db.flush()


async def _seed_weekly_reports(db: AsyncSession) -> None:
    """zhangwei 上周 1 条 submitted。"""
    last_monday = _week_monday() - timedelta(days=7)

    db.add(
        WeeklyReport(
            id=uuid4(),
            salesperson_id=USER_IDS["zhang_wei"],
            week_start=last_monday,
            summary="上周完成 5 次拜访,推进宏远、锦华两个重点客户的样板进展。",
            next_plan="本周确认宏远宽度调整样板,拜访锦华并提交新报价。",
            notes="客户对样板手感反馈良好,颜色批次稳定性需要重点关注。",
            attachments=[],
            status=WeeklyReportStatus.SUBMITTED,
        )
    )
    await db.flush()


async def _seed_samples(db: AsyncSession) -> None:
    """2 samples 留位(1A 不查,Phase 2 AI 找板用)。"""
    db.add_all([
        Sample(
            id=uuid4(),
            customer_id=CUSTOMER_IDS["hongyuan"],
            salesperson_id=USER_IDS["zhang_wei"],
            sample_no="HY-20-BK-soft",
            status=SampleStatus.ZHONGBAN,
            width="20mm",
            tension="中高",
            ribbon_type="提花织带",
            color="黑色",
            notes="手感偏软,客户主推款",
        ),
        Sample(
            id=uuid4(),
            customer_id=CUSTOMER_IDS["jinhua"],
            salesperson_id=USER_IDS["zhang_wei"],
            sample_no="JH-18-DG-rib",
            status=SampleStatus.QIYANG,
            width="18mm",
            tension="中",
            ribbon_type="罗纹织带",
            color="深灰",
        ),
    ])
    await db.flush()


# ── Entrypoint ──────────────────────────────────────────────────


async def run(if_empty: bool = False) -> None:
    async with AsyncSessionLocal() as db:
        if if_empty and not await _is_empty(db):
            print("[seed] users already exist, skipping (--if-empty mode)")
            return

        print("[seed] truncating tables...")
        await _truncate(db)

        print("[seed] users (3 sales + 1 manager + 1 boss)...")
        await _seed_users(db)

        print("[seed] customers (6 个)...")
        await _seed_customers(db)

        print("[seed] plans (zhangwei 上周 done 2 + 本周 6 + 1 个人提醒)...")
        await _seed_plans(db)

        print("[seed] visit_records (zhangwei 3 条,1 带 ai_summary)...")
        await _seed_visit_records(db)

        print("[seed] weekly_reports (zhangwei 上周 1 submitted)...")
        await _seed_weekly_reports(db)

        print("[seed] samples (2 条留位)...")
        await _seed_samples(db)

        await db.commit()
        print("[seed] ✅ done.")
        print()
        print("试点账号(密码全 123456):")
        print("  - zhangwei  / 张伟  / sales(主营客户:宏远 锦华 恒嘉)")
        print("  - liuyang   / 刘洋  / sales(主营客户:东晨 海泰)")
        print("  - chenmin   / 陈敏  / sales(主营客户:明辉)")
        print("  - wangManager / 王主管 / manager(3 sales 直属主管)")
        print()


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed dingwei-crm-sales DB")
    parser.add_argument(
        "--if-empty",
        action="store_true",
        help="只在 user 表为空时执行(docker 启动幂等)",
    )
    args = parser.parse_args()
    asyncio.run(run(if_empty=args.if_empty))
    return 0


if __name__ == "__main__":
    sys.exit(main())
