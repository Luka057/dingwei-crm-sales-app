/**
 * 「团队概览」卡片(Q1 决议 — Manager 才渲染)。
 *
 * 用原型 .focus 风格,在日历 tab 顶部。
 */
import { useQuery } from "@tanstack/react-query";
import { ArrowRight } from "lucide-react";
import { Link } from "react-router-dom";

import { api } from "../../lib/api";
import type { TeamSummary } from "../../types/api";

export function TeamOverviewCard() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["manager", "team-summary"],
    queryFn: () => api.get<TeamSummary>("/manager/team-summary"),
  });

  if (isLoading || error || !data) {
    return null;
  }

  return (
    <Link to="/app/manager/team-summary" className="focus team-overview-card">
      <div className="label" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        团队概览
        <ArrowRight size={14} />
      </div>
      <div
        className="summary"
        style={{ marginTop: 8, marginBottom: 0, gap: 8 }}
      >
        <div className="metric">
          <strong>{data.team_visits_this_week}</strong>
          <span>下属本周拜访</span>
        </div>
        <div className="metric">
          <strong style={{ color: data.team_overdue_customers > 0 ? "var(--coral)" : undefined }}>
            {data.team_overdue_customers}
          </strong>
          <span>团队超期</span>
        </div>
        <div className="metric">
          <strong style={{ color: data.pending_transfers > 0 ? "var(--coral)" : undefined }}>
            {data.pending_transfers}
          </strong>
          <span>待审转移</span>
        </div>
      </div>
    </Link>
  );
}
