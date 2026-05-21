/**
 * 日历 tab — 真数据(GET /plans/calendar)。
 *
 * Q1 决议:Manager 在顶部渲染「团队概览」卡片;Sales 不渲染。
 * 顶部还有 overdue 横幅(超期客户提醒,§4.1)。
 */
import { useQuery } from "@tanstack/react-query";
import { AlertCircle } from "lucide-react";
import { Link } from "react-router-dom";

import { TeamOverviewCard } from "../components/calendar/TeamOverviewCard";
import { api } from "../lib/api";
import { useAuthStore } from "../store/auth";
import type { CalendarResponse, OverdueSummary, PlanItem } from "../types/api";

import styles from "./CalendarPage.module.css";

export function CalendarPage() {
  const isManager = useAuthStore((s) => s.isManager());
  const today = new Date();
  const year = today.getFullYear();
  const month = today.getMonth() + 1;

  const calendarQ = useQuery({
    queryKey: ["plans", "calendar", year, month],
    queryFn: () =>
      api.get<CalendarResponse>(`/plans/calendar?year=${year}&month=${month}`),
  });

  const overdueQ = useQuery({
    queryKey: ["customers", "overdue-summary"],
    queryFn: () => api.get<OverdueSummary>("/customers/overdue-summary"),
  });

  return (
    <div className={styles.page}>
      {/* Manager 才渲染 — Q1 决议 */}
      {isManager && <TeamOverviewCard />}

      {/* 超期提醒(§4.1) */}
      {overdueQ.data && overdueQ.data.count > 0 && (
        <Link to="/app/customers?overdue=true" className={styles.overdueBanner}>
          <AlertCircle size={18} />
          <span>
            今天有 <strong>{overdueQ.data.count}</strong> 个超期客户,点击查看
          </span>
        </Link>
      )}

      <div className={styles.header}>
        <h1 className={styles.month}>
          {year} 年 {month} 月
        </h1>
        <p className={styles.subtitle}>本月日程</p>
      </div>

      {calendarQ.isLoading && <div className={styles.empty}>加载中...</div>}
      {calendarQ.error && (
        <div className={styles.empty}>加载失败,请刷新</div>
      )}

      {calendarQ.data && calendarQ.data.days.length === 0 && (
        <div className={styles.empty}>本月暂无计划,点右下角 + 新建。</div>
      )}

      {calendarQ.data?.days.map((day) => (
        <DaySection key={day.date} date={day.date} items={day.items} />
      ))}
    </div>
  );
}

function DaySection({
  date,
  items,
}: {
  date: string;
  items: PlanItem[];
}) {
  const d = new Date(date);
  const isToday = isSameDay(d, new Date());
  const wd = "日一二三四五六"[d.getDay()];

  return (
    <section className={styles.day}>
      <div className={styles.dayHeader}>
        <span className={styles.dayNum}>{d.getDate()}</span>
        <span className={styles.dayWeek}>周{wd}</span>
        {isToday && <span className={styles.todayPill}>今天</span>}
      </div>
      <div className={styles.items}>
        {items.map((p) => (
          <PlanCard key={p.id} plan={p} />
        ))}
      </div>
    </section>
  );
}

function PlanCard({ plan }: { plan: PlanItem }) {
  const time = new Date(plan.scheduled_at).toLocaleTimeString("zh-CN", {
    hour: "2-digit",
    minute: "2-digit",
  });
  const statusLabel = {
    pending: "待办",
    done: "已完成",
    cancelled: "已取消",
  }[plan.status];

  return (
    <article
      className={`${styles.plan} ${
        plan.is_personal ? styles.personal : ""
      } ${styles[`status_${plan.status}`]}`}
    >
      <div className={styles.planTop}>
        <span className={styles.planTime}>{time}</span>
        <span className={styles.planType}>
          {plan.type === "visit" ? "拜访" : "自定义"}
          {plan.is_personal && " · 个人"}
        </span>
        <span className={styles.planStatus}>{statusLabel}</span>
      </div>
      <h3 className={styles.planTitle}>
        {plan.customer_name ? (
          <>
            <strong>{plan.customer_name}</strong>
            <span className={styles.planSubTitle}> · {plan.title}</span>
          </>
        ) : (
          plan.title
        )}
      </h3>
      {plan.content && <p className={styles.planContent}>{plan.content}</p>}
    </article>
  );
}

function isSameDay(a: Date, b: Date): boolean {
  return (
    a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate()
  );
}
