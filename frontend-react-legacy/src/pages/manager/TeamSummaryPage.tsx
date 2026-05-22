/**
 * 主管视图子页 — 团队概览(Q1 决议)。
 * 路由:/app/manager/team-summary
 */
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft } from "lucide-react";
import { Link } from "react-router-dom";

import { api } from "../../lib/api";
import { useAuthStore } from "../../store/auth";
import type { TeamSummary } from "../../types/api";

export function TeamSummaryPage() {
  const isManager = useAuthStore((s) => s.isManager());

  const { data, isLoading, error } = useQuery({
    queryKey: ["manager", "team-summary"],
    queryFn: () => api.get<TeamSummary>("/manager/team-summary"),
    enabled: isManager,
  });

  if (!isManager) {
    return (
      <div className="page active">
        <div className="page-title">
          <h2>无权访问</h2>
          <p>
            本页面仅限主管访问。<Link to="/app/calendar">返回日历</Link>
          </p>
        </div>
      </div>
    );
  }
  if (isLoading) return <div className="page active"><p className="empty-day">加载中...</p></div>;
  if (error || !data)
    return <div className="page active"><p className="empty-day">加载失败</p></div>;

  return (
    <div className="page active">
      <div className="page-title">
        <div>
          <Link to="/app/calendar" className="chip" style={{ display: "inline-flex", gap: 4, alignItems: "center" }}>
            <ArrowLeft size={14} /> 日历
          </Link>
          <h2 style={{ marginTop: 8 }}>团队概览</h2>
          <p>下属本周状态 + 待审转移</p>
        </div>
      </div>

      <div className="summary">
        <div className="metric">
          <strong>{data.team_visits_this_week}</strong>
          <span>本周拜访</span>
        </div>
        <div className="metric">
          <strong
            style={{
              color: data.team_overdue_customers > 0 ? "var(--coral)" : undefined,
            }}
          >
            {data.team_overdue_customers}
          </strong>
          <span>超期客户</span>
        </div>
        <div className="metric">
          <strong
            style={{ color: data.pending_transfers > 0 ? "var(--coral)" : undefined }}
          >
            {data.pending_transfers}
          </strong>
          <span>待审转移</span>
        </div>
      </div>

      <div className="section-head">
        <h2>下属</h2>
        <span>{data.subordinates.length} 人</span>
      </div>

      <div className="customer-list">
        {data.subordinates.map((s) => (
          <article key={s.user_id} className="customer-card">
            <div className="card-head">
              <strong>{s.name}</strong>
              <span style={{ fontSize: 11, color: "var(--muted)" }}>
                @{s.username}
              </span>
            </div>
            <div className="subline">
              <span>本周拜访 {s.visits_this_week}</span>
              <span
                className={`tag ${s.overdue_customers > 0 ? "warning" : ""}`}
              >
                超期 {s.overdue_customers}
              </span>
            </div>
          </article>
        ))}
      </div>

      <p className="empty-day" style={{ marginTop: 16 }}>
        下属拜访详情 / 转移审批操作 Phase 1B 完整 UI 实现。
      </p>
    </div>
  );
}
