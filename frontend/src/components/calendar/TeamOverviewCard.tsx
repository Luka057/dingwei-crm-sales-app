/**
 * 「团队概览」卡片(Q1 决议 — Manager 才渲染)。
 *
 * 位置:日历 tab 顶部
 * 数据源:GET /api/v1/manager/team-summary
 * 点击进入主管视图子页 /app/manager/team-summary
 */
import { useQuery } from "@tanstack/react-query";
import { ArrowRight, Users, Clock, GitPullRequestArrow } from "lucide-react";
import { Link } from "react-router-dom";

import { api } from "../../lib/api";
import type { TeamSummary } from "../../types/api";

import styles from "./TeamOverviewCard.module.css";

export function TeamOverviewCard() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["manager", "team-summary"],
    queryFn: () => api.get<TeamSummary>("/manager/team-summary"),
  });

  if (isLoading) {
    return <div className={styles.card}>团队概览加载中...</div>;
  }
  if (error || !data) {
    return null; // Manager 但拿不到数据时不渲染(权限 / 网络)
  }

  return (
    <Link to="/app/manager/team-summary" className={styles.card}>
      <div className={styles.header}>
        <span className={styles.eyebrow}>团队概览</span>
        <ArrowRight size={18} />
      </div>
      <div className={styles.metrics}>
        <Metric
          icon={Users}
          label="下属本周拜访"
          value={data.team_visits_this_week}
        />
        <Metric
          icon={Clock}
          label="团队超期客户"
          value={data.team_overdue_customers}
          highlight={data.team_overdue_customers > 0}
        />
        <Metric
          icon={GitPullRequestArrow}
          label="待审转移"
          value={data.pending_transfers}
          highlight={data.pending_transfers > 0}
        />
      </div>
    </Link>
  );
}

function Metric({
  icon: Icon,
  label,
  value,
  highlight,
}: {
  icon: typeof Users;
  label: string;
  value: number;
  highlight?: boolean;
}) {
  return (
    <div className={styles.metric}>
      <Icon size={16} />
      <div className={styles.metricBody}>
        <span className={styles.metricLabel}>{label}</span>
        <span
          className={`${styles.metricValue} ${
            highlight ? styles.highlight : ""
          }`}
        >
          {value}
        </span>
      </div>
    </div>
  );
}
