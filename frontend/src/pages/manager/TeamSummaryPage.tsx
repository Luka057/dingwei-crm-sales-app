/**
 * 主管视图子页 — 团队概览。
 * 路由:/app/manager/team-summary(Q1 决议)
 */
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft } from "lucide-react";
import { Link } from "react-router-dom";

import { api } from "../../lib/api";
import { useAuthStore } from "../../store/auth";
import type { TeamSummary } from "../../types/api";

import styles from "./TeamSummaryPage.module.css";

export function TeamSummaryPage() {
  const isManager = useAuthStore((s) => s.isManager());

  const { data, isLoading, error } = useQuery({
    queryKey: ["manager", "team-summary"],
    queryFn: () => api.get<TeamSummary>("/manager/team-summary"),
    enabled: isManager,
  });

  if (!isManager) {
    return (
      <div className={styles.deny}>
        本页面仅限主管访问。<Link to="/app/calendar">返回日历</Link>
      </div>
    );
  }
  if (isLoading) return <div className={styles.loading}>加载中...</div>;
  if (error || !data) return <div className={styles.loading}>加载失败</div>;

  return (
    <div className={styles.page}>
      <div className={styles.headerRow}>
        <Link to="/app/calendar" className={styles.back}>
          <ArrowLeft size={16} />
          日历
        </Link>
        <h1 className={styles.title}>团队概览</h1>
      </div>

      <div className={styles.summary}>
        <SummaryCard
          label="本周拜访"
          value={data.team_visits_this_week}
        />
        <SummaryCard
          label="超期客户"
          value={data.team_overdue_customers}
          danger={data.team_overdue_customers > 0}
        />
        <SummaryCard
          label="待审转移"
          value={data.pending_transfers}
          danger={data.pending_transfers > 0}
        />
      </div>

      <h2 className={styles.subhead}>下属</h2>
      <ul className={styles.subs}>
        {data.subordinates.map((s) => (
          <li key={s.user_id} className={styles.sub}>
            <div className={styles.subName}>
              <strong>{s.name}</strong>
              <span className={styles.subUsername}>@{s.username}</span>
            </div>
            <div className={styles.subMetrics}>
              <span>本周拜访 {s.visits_this_week}</span>
              <span
                className={
                  s.overdue_customers > 0 ? styles.metricDanger : undefined
                }
              >
                超期 {s.overdue_customers}
              </span>
            </div>
          </li>
        ))}
      </ul>

      <p className={styles.note}>
        点下属进入详细拜访列表 / 处理待审转移的页面留 Phase 1B。
      </p>
    </div>
  );
}

function SummaryCard({
  label,
  value,
  danger,
}: {
  label: string;
  value: number;
  danger?: boolean;
}) {
  return (
    <div className={styles.card}>
      <span className={styles.cardLabel}>{label}</span>
      <span className={`${styles.cardValue} ${danger ? styles.danger : ""}`}>
        {value}
      </span>
    </div>
  );
}
