/**
 * 客户 tab — 原型同款视觉,接真数据。
 *
 * 结构(对齐 prototype customersPage.html):
 *   .page#customersPage
 *     .page-title   标题 + 描述 + 搜索 chip
 *     .summary      3 个 metric(负责客户 / A 类 / 需跟进)
 *     .filter-row   chip:全部 / 超期 / A 类 / 样板中 / 本周拜访
 *     .customer-list  .customer-card * N
 */
import { useQuery } from "@tanstack/react-query";
import { useSearchParams } from "react-router-dom";

import { api } from "../lib/api";
import type { CustomerListItem } from "../types/api";

type Filter = "all" | "overdue" | "a" | "sample" | "week";

const FILTERS: { key: Filter; label: string }[] = [
  { key: "all", label: "全部" },
  { key: "overdue", label: "超期" },
  { key: "a", label: "A 类" },
  { key: "sample", label: "样板中" },
  { key: "week", label: "本周拜访" },
];

export function CustomersPage() {
  const [params, setParams] = useSearchParams();
  const overdueParam = params.get("overdue") === "true";
  const filter: Filter = overdueParam
    ? "overdue"
    : (params.get("f") as Filter) || "all";

  // 一次性拉所有客户,过滤在 Python 侧
  const { data, isLoading } = useQuery({
    queryKey: ["customers", "list", filter === "overdue" ? "overdue" : "all"],
    queryFn: () =>
      api.get<CustomerListItem[]>(
        filter === "overdue" ? "/customers/?overdue=true" : "/customers/"
      ),
  });

  const setFilter = (f: Filter) => {
    if (f === "overdue") setParams({ overdue: "true" });
    else if (f === "all") setParams({});
    else setParams({ f });
  };

  const customers = data ?? [];
  // 客户端二次过滤(a / sample / week)
  const filtered = customers.filter((c) => {
    if (filter === "a") return c.level === "A";
    if (filter === "sample") return c.tags.includes("sample");
    if (filter === "week") return c.tags.includes("week");
    return true;
  });

  const aCount = customers.filter((c) => c.level === "A").length;
  const overdueCount = customers.filter((c) => c.is_overdue).length;

  return (
    <div className="page active" id="customersPage">
      <div className="page-title">
        <div>
          <h2>我的客户</h2>
          <p>只看自己负责的客户,按跟进压力排序。</p>
        </div>
        <button className="chip primary" type="button">
          搜索
        </button>
      </div>

      <div className="summary">
        <div className="metric">
          <strong>{customers.length}</strong>
          <span>负责客户</span>
        </div>
        <div className="metric">
          <strong>{aCount}</strong>
          <span>A 类客户</span>
        </div>
        <div className="metric">
          <strong style={{ color: overdueCount > 0 ? "var(--coral)" : undefined }}>
            {overdueCount}
          </strong>
          <span>需跟进</span>
        </div>
      </div>

      <div className="filter-row">
        {FILTERS.map((f) => (
          <button
            key={f.key}
            className={`chip ${filter === f.key ? "primary" : ""}`}
            onClick={() => setFilter(f.key)}
            type="button"
          >
            {f.label}
          </button>
        ))}
      </div>

      <div className="customer-list">
        {isLoading && <p className="empty-day">加载中...</p>}
        {!isLoading && filtered.length === 0 && (
          <p className="empty-day">没有符合条件的客户</p>
        )}
        {filtered.map((c) => (
          <CustomerCard key={c.id} c={c} />
        ))}
      </div>
    </div>
  );
}

function CustomerCard({ c }: { c: CustomerListItem }) {
  const lastVisit = c.last_visit_at
    ? new Date(c.last_visit_at).toLocaleDateString("zh-CN", {
        month: "short",
        day: "numeric",
      })
    : "未拜访";

  const daysAgo = c.last_visit_at
    ? Math.floor(
        (Date.now() - new Date(c.last_visit_at).getTime()) / 86400000
      )
    : null;

  return (
    <article className={`customer-card level-${c.level.toLowerCase()}`}>
      <div className="card-head">
        <strong>{c.name}</strong>
        <span className={`level-badge level-${c.level.toLowerCase()}`}>
          {c.level}
        </span>
      </div>
      <p className="card-meta">
        {c.contact_name && <span>{c.contact_name}</span>}
        {c.phone && <span> · {c.phone}</span>}
      </p>
      <div className="subline">
        <span>
          上次拜访:{lastVisit}
          {daysAgo !== null && ` · ${daysAgo} 天前`}
        </span>
        {c.is_overdue && <span className="tag warning">超期</span>}
        {c.tags.includes("sample") && <span className="tag">样板中</span>}
        {c.tags.includes("week") && <span className="tag">本周拜访</span>}
      </div>
    </article>
  );
}
