/**
 * 周报 tab — 占位 + 拉自己周报列表。
 *
 * 1A 仅列表;创建/编辑/submit/reopen 全 UI 在 Phase 1B 补,接口已就绪。
 */
import { useQuery } from "@tanstack/react-query";

import { api } from "../lib/api";

import styles from "./placeholder.module.css";

interface WeeklyReport {
  id: string;
  week_start: string;
  status: "draft" | "submitted" | "reopened";
  summary: string | null;
}

export function ReportsPage() {
  const { data } = useQuery({
    queryKey: ["weekly-reports", "list"],
    queryFn: () => api.get<WeeklyReport[]>("/weekly-reports/"),
  });

  return (
    <div className={styles.page}>
      <h1>周报</h1>
      <p className={styles.subtitle}>本周 / 历史周报</p>

      <ul className={styles.list}>
        {data?.map((r) => (
          <li key={r.id} className={styles.item}>
            <div className={styles.row}>
              <strong>{r.week_start}</strong>
              <span
                className={`${styles.badge} ${styles[`status_${r.status}`]}`}
              >
                {
                  { draft: "草稿", submitted: "已提交", reopened: "已退回" }[
                    r.status
                  ]
                }
              </span>
            </div>
            {r.summary && (
              <p className={styles.summary}>
                {r.summary.length > 80
                  ? r.summary.slice(0, 80) + "..."
                  : r.summary}
              </p>
            )}
          </li>
        ))}
      </ul>

      <p className={styles.note}>
        1A 占位 — 创建 / AI 草稿 / 提交 / 退回交互在 Phase 1B 实现。
        接口已就绪(submit / reopen / generate-ai-draft)。
      </p>
    </div>
  );
}
