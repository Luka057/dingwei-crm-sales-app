/**
 * 日历 tab — 原型同款视觉,接真数据。
 *
 * 结构(对齐 prototype calendarPage.html):
 *   .page#calendarPage
 *     .summary             顶部 3 个 metric(今日动作 / 建议跟进 / 已完成)
 *     .quick-grid          4 个快捷按钮(计划 / 找客户 / AI / 周报)
 *     section.focus        AI 今日建议卡(超期最紧的 1 个客户)
 *     .section-head        "时间线" + 安排按钮
 *     section.timeline     按日 .agenda-day 渲染
 *
 * Q1:Manager 顶部加「团队概览」卡(用原型 .focus 风格的 mini card)。
 */
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { TeamOverviewCard } from "../components/calendar/TeamOverviewCard";
import { api } from "../lib/api";
import { useAuthStore } from "../store/auth";
import { useSheetStore } from "../store/sheets";
import type {
  CalendarResponse,
  OverdueSummary,
  PlanItem,
} from "../types/api";

const WEEKDAY = "日一二三四五六";

function fmtDate(d: Date): string {
  const wd = WEEKDAY[d.getDay()];
  return `${d.getMonth() + 1} 月 ${d.getDate()} 日 · 周${wd}`;
}

function fmtTime(iso: string): string {
  const d = new Date(iso);
  const hh = String(d.getHours()).padStart(2, "0");
  const mm = String(d.getMinutes()).padStart(2, "0");
  return `${hh}:${mm}`;
}

function isSameDay(a: Date, b: Date) {
  return (
    a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate()
  );
}

export function CalendarPage() {
  const isManager = useAuthStore((s) => s.isManager());
  const openSheet = useSheetStore((s) => s.openSheet);
  const today = new Date();

  const calQ = useQuery({
    queryKey: ["plans", "calendar", today.getFullYear(), today.getMonth() + 1],
    queryFn: () =>
      api.get<CalendarResponse>(
        `/plans/calendar?year=${today.getFullYear()}&month=${today.getMonth() + 1}`
      ),
  });

  const overdueQ = useQuery({
    queryKey: ["customers", "overdue-summary"],
    queryFn: () => api.get<OverdueSummary>("/customers/overdue-summary"),
  });

  // 计算顶部 metric
  const allPlans = (calQ.data?.days ?? []).flatMap((d) => d.items);
  const todayPlans = (calQ.data?.days ?? [])
    .filter((d) => isSameDay(new Date(d.date), today))
    .flatMap((d) => d.items);

  const planCount = todayPlans.length;
  const doneCount = todayPlans.filter((p) => p.status === "done").length;
  const riskCount = overdueQ.data?.count ?? 0;

  // AI 今日建议(用最紧急的超期客户做 mock 文案,Phase 1B 接 DeepSeek)
  const topOverdue = overdueQ.data?.items[0];
  const focusTitle = topOverdue
    ? `优先跟进 ${topOverdue.name}`
    : "今日无超期客户,按计划推进";
  const focusText = topOverdue
    ? `${topOverdue.name} 已超期${
        topOverdue.last_visit_at
          ? Math.floor(
              (Date.now() - new Date(topOverdue.last_visit_at).getTime()) /
                86400000
            ) + " 天"
          : "(从未拜访)"
      }未拜访,建议优先安排。AI 建议接入 DeepSeek 后,会基于拜访记录给出更具体的跟进建议。`
    : "保持现有节奏。AI 草稿会随拜访数据积累自动给出更精准的建议(Phase 1B 接入)。";

  return (
    <div className="page active" id="calendarPage">
      {isManager && <TeamOverviewCard />}

      <div className="summary">
        <div className="metric">
          <strong>{planCount}</strong>
          <span>今日动作</span>
        </div>
        <div className="metric">
          <strong>{riskCount}</strong>
          <span>建议跟进</span>
        </div>
        <div className="metric">
          <strong>{doneCount}</strong>
          <span>已完成</span>
        </div>
      </div>

      <div className="quick-grid">
        {/* 对齐原型:计划 / 找客户 / AI / 周报 */}
        <button className="quick" onClick={() => openSheet("plan")}>
          <svg viewBox="0 0 24 24">
            <path d="M12 5v14M5 12h14" />
          </svg>
          <span>计划</span>
        </button>
        <Link to="/app/customers" className="quick">
          <svg viewBox="0 0 24 24">
            <circle cx="11" cy="11" r="7" />
            <path d="m20 20-3.5-3.5" />
          </svg>
          <span>找客户</span>
        </Link>
        <Link to="/app/ai" className="quick">
          <svg viewBox="0 0 24 24">
            <path d="M12 3l1.7 5.3L19 10l-5.3 1.7L12 17l-1.7-5.3L5 10l5.3-1.7L12 3Z" />
            <path d="M19 15l.8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8L19 15Z" />
          </svg>
          <span>AI</span>
        </Link>
        <Link to="/app/reports" className="quick">
          <svg viewBox="0 0 24 24">
            <path d="M8 6h13" />
            <path d="M8 12h13" />
            <path d="M8 18h13" />
            <path d="M3 6h.01" />
            <path d="M3 12h.01" />
            <path d="M3 18h.01" />
          </svg>
          <span>周报</span>
        </Link>
      </div>

      <section className="focus">
        <div className="label">AI 今日建议</div>
        <h2>{focusTitle}</h2>
        <p>{focusText}</p>
        <div className="actions" style={{ marginTop: 12 }}>
          <button
            type="button"
            className="chip primary"
            onClick={() => openSheet("visit")}
          >
            记录拜访
          </button>
          {topOverdue && (
            <Link to="/app/customers?overdue=true" className="chip">
              查看全部超期({riskCount})
            </Link>
          )}
        </div>
      </section>

      <div className="section-head">
        <h2>本月时间线</h2>
        <span>{allPlans.length} 项</span>
      </div>

      <section className="timeline">
        {calQ.isLoading && <div className="empty-day">加载中...</div>}
        {calQ.data && calQ.data.days.length === 0 && (
          <div className="empty-day">本月暂无计划</div>
        )}
        {calQ.data?.days.map((day) => {
          const dDate = new Date(day.date);
          return (
            <section
              key={day.date}
              className={`agenda-day ${isSameDay(dDate, today) ? "today" : ""} ${
                day.items.length === 0 ? "empty" : ""
              }`}
            >
              <header>
                <strong>{fmtDate(dDate)}</strong>
                {isSameDay(dDate, today) && <em>今天</em>}
              </header>
              {day.items.length === 0 ? (
                <p className="empty-day">无安排</p>
              ) : (
                <ul>
                  {day.items.map((p) => (
                    <PlanRow key={p.id} plan={p} />
                  ))}
                </ul>
              )}
            </section>
          );
        })}
      </section>
    </div>
  );
}

function PlanRow({ plan }: { plan: PlanItem }) {
  const openSheet = useSheetStore((s) => s.openSheet);
  // 原型用 article.event > .event-card.{type} > .event-title + p > .event-time + desc
  const cardType = plan.is_personal
    ? "personal"
    : plan.type === "visit"
    ? "visit"
    : "custom";
  return (
    <article
      className="event"
      data-status={plan.status}
      onClick={() => openSheet("planDetail", { plan })}
      style={{ cursor: "pointer" }}
    >
      <div className={`event-card ${cardType}`}>
        <div className="event-title">
          {plan.customer_name ? (
            <strong>{plan.customer_name}</strong>
          ) : (
            <strong>{plan.title}</strong>
          )}
          {plan.customer_name && <span>{plan.title}</span>}
          {plan.is_personal && (
            <span className="badge personal-badge">个人</span>
          )}
          {plan.type === "visit" && !plan.is_personal && (
            <span className="badge visit-badge">拜访</span>
          )}
          {plan.status === "done" && (
            <span className="badge done-badge">✓ 已完成</span>
          )}
          {plan.status === "cancelled" && (
            <span className="badge cancelled-badge">已取消</span>
          )}
        </div>
        <p>
          <span className="event-time">{fmtTime(plan.scheduled_at)}</span>
          {plan.content || (plan.customer_name ? "" : " · 无备注")}
        </p>
      </div>
    </article>
  );
}
