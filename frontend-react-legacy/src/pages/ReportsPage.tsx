/**
 * 周报 tab — 原型同款 .report-card 视觉。
 *
 * 结构(对齐 prototype reportsPage.html):
 *   .page-title    标题 + 描述 + 录入 chip
 *   .report-list   .report-card.pending(待提交) + 历史已提交卡
 */
import { useQuery } from "@tanstack/react-query";

import { api } from "../lib/api";

interface WeeklyReport {
  id: string;
  salesperson_id: string;
  salesperson_name: string | null;
  week_start: string;
  summary: string | null;
  next_plan: string | null;
  notes: string | null;
  status: "draft" | "submitted" | "reopened";
  created_at: string;
  updated_at: string;
}

const STATUS_LABEL = {
  draft: "草稿",
  submitted: "已提交",
  reopened: "已退回",
} as const;

function fmtWeek(weekStart: string): string {
  const d = new Date(weekStart);
  const yr = d.getFullYear();
  // ISO week number
  const target = new Date(d.valueOf());
  const dayNr = (d.getDay() + 6) % 7;
  target.setDate(target.getDate() - dayNr + 3);
  const firstThursday = new Date(target.getFullYear(), 0, 4);
  const wk =
    1 +
    Math.round(
      ((target.getTime() - firstThursday.getTime()) / 86400000 -
        3 +
        ((firstThursday.getDay() + 6) % 7)) /
        7
    );
  return `${yr} 第 ${wk} 周`;
}

export function ReportsPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["weekly-reports", "list"],
    queryFn: () => api.get<WeeklyReport[]>("/weekly-reports/"),
  });

  const all = data ?? [];
  const draftOrReopened = all.find(
    (r) => r.status === "draft" || r.status === "reopened"
  );
  const submitted = all.filter((r) => r.status === "submitted");

  return (
    <div className="page active" id="reportsPage">
      <div className="page-title">
        <div>
          <h2>周报</h2>
          <p>历史周报会同步到老板端,新周报按固定 4 段录入。</p>
        </div>
        <button className="chip primary" type="button">
          录入
        </button>
      </div>

      <div className="report-list">
        {isLoading && <p className="empty-day">加载中...</p>}

        {/* 当周(草稿/退回)或没有当周 */}
        {draftOrReopened ? (
          <article
            className={`report-card pending ${
              draftOrReopened.status === "reopened" ? "reopened" : ""
            }`}
          >
            <div className="card-head">
              <strong>本周周报</strong>
              <span className="report-date">
                {STATUS_LABEL[draftOrReopened.status]}
              </span>
            </div>
            <p>
              {draftOrReopened.summary
                ? draftOrReopened.summary.length > 100
                  ? draftOrReopened.summary.slice(0, 100) + "..."
                  : draftOrReopened.summary
                : "AI 草稿可基于本周拜访 + 计划自动生成 4 段(总结/下周计划/备注/附件),可继续补充。"}
            </p>
            <div className="actions">
              <button className="chip primary" type="button">
                {draftOrReopened.status === "reopened" ? "补充提交" : "继续填写"}
              </button>
              <button className="chip" type="button">
                AI 草稿
              </button>
            </div>
          </article>
        ) : (
          <article className="report-card pending">
            <div className="card-head">
              <strong>本周周报</strong>
              <span className="report-date">未创建</span>
            </div>
            <p>
              本周还没有周报草稿。点 "录入" 开始写,或让 AI 基于本周拜访生成草稿。
            </p>
            <div className="actions">
              <button className="chip primary" type="button">
                开始录入
              </button>
              <button className="chip" type="button">
                AI 草稿
              </button>
            </div>
          </article>
        )}

        {/* 历史已提交 */}
        {submitted.map((r) => (
          <article key={r.id} className="report-card">
            <div className="card-head">
              <strong>{fmtWeek(r.week_start)}</strong>
              <span className="report-date">{STATUS_LABEL[r.status]}</span>
            </div>
            <p>
              {r.summary
                ? r.summary.length > 90
                  ? r.summary.slice(0, 90) + "..."
                  : r.summary
                : "(本期未填总结)"}
            </p>
            <div className="subline">
              <span>{r.summary ? "总结 ✓" : "总结 —"}</span>
              <span>{r.next_plan ? "下周计划 ✓" : "下周计划 —"}</span>
              <span>{r.notes ? "备注 ✓" : "备注 —"}</span>
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}
