/**
 * 拜访详情 sheet — 原型 visitDetailSheet 的 React 化。
 *
 * 打开方式:openSheet("visitDetail", { record, customer_name })
 *   1A 没有 GET /visit-records/{id} 端点,所以详情数据直接用列表传入的
 *   VisitRecordSummary(content_preview + ai_summary)。
 *
 * 字段对齐原型:客户 / 方式 / 拜访时间 / 拜访对象 / 拜访内容 / AI 摘要。
 */
import { INTENTION_LABEL, METHOD_LABEL, fmtDateTime } from "../../lib/labels";
import { useSheetStore } from "../../store/sheets";
import type { VisitRecordSummary } from "../../types/api";
import { Sheet } from "../sheet/Sheet";

interface VisitDetailPayload {
  record: VisitRecordSummary;
  customer_name: string;
}

export function VisitDetailSheet() {
  const payload = useSheetStore((s) => s.payload) as VisitDetailPayload | null;
  const openSheet = useSheetStore((s) => s.openSheet);
  const r = payload?.record;

  return (
    <Sheet name="visitDetail" title="拜访详情">
      {r && (
        <>
          <div className="customer-detail-card">
            <div className="detail-title">
              <h3>{payload?.customer_name ?? "客户"}</h3>
              <span className="level-pill">{METHOD_LABEL[r.method]}</span>
            </div>
            <div className="detail-grid">
              <div className="detail-field">
                <span>拜访时间</span>
                <b>{fmtDateTime(r.visit_at)}</b>
              </div>
              <div className="detail-field">
                <span>客户意向</span>
                <b>{INTENTION_LABEL[r.intention]}</b>
              </div>
              <div className="detail-field">
                <span>拜访对象</span>
                <b>{r.target_person || "—"}</b>
              </div>
              <div className="detail-field">
                <span>现场照片</span>
                <b>{r.has_attachments ? "有" : "无"}</b>
              </div>
              <div className="detail-field full">
                <span>拜访内容</span>
                <b>{r.content_preview}</b>
              </div>
              {r.ai_summary && (
                <div className="detail-field full">
                  <span>AI 摘要</span>
                  <b>{r.ai_summary}</b>
                </div>
              )}
            </div>
          </div>

          <div className="actions">
            <button
              type="button"
              className="chip primary"
              onClick={() =>
                openSheet("visit", {
                  customer_name: payload?.customer_name,
                })
              }
            >
              补充记录
            </button>
          </div>
        </>
      )}
    </Sheet>
  );
}
