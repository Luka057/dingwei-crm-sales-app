/**
 * 客户 tab — 占位:列表 + 总数 + 超期筛选。
 *
 * 1A:仅展示自己客户(GET /customers),不开 360 详情完整 UI(Phase 1B 补)。
 */
import { useQuery } from "@tanstack/react-query";
import { useSearchParams } from "react-router-dom";

import { api } from "../lib/api";
import type { CustomerListItem } from "../types/api";

import styles from "./CustomersPage.module.css";

export function CustomersPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const overdue = searchParams.get("overdue") === "true";

  const queryStr = overdue ? "?overdue=true" : "";
  const { data, isLoading } = useQuery({
    queryKey: ["customers", "list", overdue],
    queryFn: () => api.get<CustomerListItem[]>(`/customers/${queryStr}`),
  });

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1>客户</h1>
        <p className={styles.count}>
          {isLoading ? "加载中" : `${data?.length ?? 0} 个`}
          {overdue && " · 仅超期"}
        </p>
      </div>

      <div className={styles.filters}>
        <button
          className={`${styles.chip} ${!overdue ? styles.chipActive : ""}`}
          onClick={() => setSearchParams({})}
        >
          全部
        </button>
        <button
          className={`${styles.chip} ${overdue ? styles.chipActive : ""}`}
          onClick={() => setSearchParams({ overdue: "true" })}
        >
          超期
        </button>
      </div>

      <ul className={styles.list}>
        {data?.map((c) => (
          <li key={c.id} className={styles.item}>
            <div className={styles.row}>
              <span className={`${styles.level} ${styles[`level_${c.level}`]}`}>
                {c.level}
              </span>
              <strong className={styles.name}>{c.name}</strong>
              {c.is_overdue && <span className={styles.overduePill}>超期</span>}
            </div>
            <div className={styles.meta}>
              {c.contact_name && <span>{c.contact_name}</span>}
              {c.phone && <span>· {c.phone}</span>}
              {c.last_visit_at && (
                <span>
                  · 最近拜访 {new Date(c.last_visit_at).toLocaleDateString()}
                </span>
              )}
              {!c.last_visit_at && <span className={styles.muted}>· 未拜访</span>}
            </div>
          </li>
        ))}
      </ul>

      <p className={styles.note}>
        1A 仅展示列表,客户 360 / 拜访录入 / 申请转移在 Phase 1B 完整实现。
      </p>
    </div>
  );
}
