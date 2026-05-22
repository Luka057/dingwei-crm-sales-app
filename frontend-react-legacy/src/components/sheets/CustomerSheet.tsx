/**
 * 客户 360 sheet — 原型 customerSheet 的 React 化。
 *
 * 打开方式:openSheet("customer", { customer_id })
 *   → GET /customers/{id} 拉详情(基本资料 + KPI + 拜访时间线)
 *
 * 结构对齐原型:
 *   .customer-detail-card  基本资料(简称/负责销售/联系人/电话/地址 + last-visit-bar)
 *   .detail-kpis           拜访次数 / 起板数 / 转单数 / 转化率
 *   .visit-feed            拜访时间线(点条目 → visitDetail sheet)
 *   .actions               记录拜访 / 安排跟进 / 问 AI(+ Q2 更多菜单后续加)
 */
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";

import { api } from "../../lib/api";
import {
  INTENTION_LABEL,
  METHOD_LABEL,
  daysSince,
  fmtDate,
  fmtDateTime,
} from "../../lib/labels";
import { useSheetStore } from "../../store/sheets";
import type { CustomerDetail, VisitRecordSummary } from "../../types/api";
import { Sheet } from "../sheet/Sheet";

interface CustomerSheetPayload {
  customer_id: string;
}

export function CustomerSheet() {
  const isActive = useSheetStore((s) => s.activeSheet === "customer");
  const payload = useSheetStore((s) => s.payload) as CustomerSheetPayload | null;
  const openSheet = useSheetStore((s) => s.openSheet);
  const navigate = useNavigate();
  const customerId = payload?.customer_id;

  const detailQ = useQuery({
    queryKey: ["customers", "detail", customerId],
    queryFn: () => api.get<CustomerDetail>(`/customers/${customerId}`),
    enabled: isActive && !!customerId,
  });

  const c = detailQ.data;
  const days = daysSince(c?.last_visit_at ?? null);

  return (
    <Sheet name="customer" title="客户 360">
      {detailQ.isLoading && <p className="empty-day">加载中...</p>}
      {detailQ.isError && <p className="empty-day">加载失败,请重试</p>}

      {c && (
        <>
          <div className="customer-detail-card">
            <div className="detail-title">
              <h3>{c.name}</h3>
              <span className="level-pill">{c.level} 类客户</span>
            </div>
            <div className="detail-grid">
              <div className="detail-field">
                <span>简称</span>
                <b>{c.short_name || "—"}</b>
              </div>
              <div className="detail-field">
                <span>联系人</span>
                <b>
                  {c.contact_name || "—"}
                  {c.contact_title ? ` · ${c.contact_title}` : ""}
                </b>
              </div>
              <div className="detail-field">
                <span>电话</span>
                <b>{c.phone || "—"}</b>
              </div>
              <div className="detail-field">
                <span>状态</span>
                <b>{c.is_overdue ? "需跟进" : "正常"}</b>
              </div>
              <div className="detail-field full">
                <span>地址</span>
                <b>{c.address || "—"}</b>
              </div>
            </div>
            <div className="last-visit-bar">
              <div>
                <span>最近拜访</span>
                <b>{c.last_visit_at ? fmtDate(c.last_visit_at) : "未拜访"}</b>
              </div>
              <div>
                <strong>{days ?? "—"}</strong>
                <em>天前</em>
              </div>
            </div>
          </div>

          <div className="detail-kpis">
            <div className="detail-kpi">
              <strong>{c.kpis.visits}</strong>
              <span>拜访次数</span>
            </div>
            <div className="detail-kpi">
              <strong>{c.kpis.samples}</strong>
              <span>起板数</span>
            </div>
            <div className="detail-kpi">
              <strong>{c.kpis.orders}</strong>
              <span>转单数</span>
            </div>
            <div className="detail-kpi">
              <strong>{Math.round(c.kpis.conversion_rate * 100)}%</strong>
              <span>转化率</span>
            </div>
          </div>

          <div
            className="section-head"
            style={{ marginTop: 18, marginBottom: 8 }}
          >
            <h2>拜访时间线</h2>
            <button
              type="button"
              onClick={() =>
                openSheet("visit", {
                  customer_id: c.id,
                  customer_name: c.name,
                })
              }
            >
              新增
            </button>
          </div>

          <div className="visit-feed">
            {c.visit_records.length === 0 && (
              <p className="empty-day">还没有拜访记录</p>
            )}
            {c.visit_records.map((r) => (
              <VisitItem
                key={r.id}
                r={r}
                onOpen={() =>
                  openSheet("visitDetail", {
                    record: r,
                    customer_name: c.name,
                  })
                }
              />
            ))}
          </div>

          <div className="actions">
            <button
              type="button"
              className="chip primary"
              onClick={() =>
                openSheet("visit", {
                  customer_id: c.id,
                  customer_name: c.name,
                })
              }
            >
              记录拜访
            </button>
            <button
              type="button"
              className="chip"
              onClick={() =>
                openSheet("plan", {
                  customer_id: c.id,
                  customer_name: c.name,
                })
              }
            >
              安排跟进
            </button>
            <button
              type="button"
              className="chip"
              onClick={() => {
                useSheetStore.getState().closeSheets();
                navigate(`/app/ai?customer=${encodeURIComponent(c.name)}`);
              }}
            >
              问 AI
            </button>
          </div>
        </>
      )}
    </Sheet>
  );
}

function VisitItem({
  r,
  onOpen,
}: {
  r: VisitRecordSummary;
  onOpen: () => void;
}) {
  return (
    <article className="visit-item">
      <div className="visit-meta">
        <span>{fmtDateTime(r.visit_at)}</span>
        <span className="method-pill">{METHOD_LABEL[r.method]}</span>
        <span>{INTENTION_LABEL[r.intention]}</span>
      </div>
      <p>{r.content_preview}</p>
      <button type="button" className="visit-link" onClick={onOpen}>
        点击查看详情 -&gt;
      </button>
    </article>
  );
}
