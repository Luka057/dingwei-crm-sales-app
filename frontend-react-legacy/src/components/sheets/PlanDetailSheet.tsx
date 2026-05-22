/**
 * 计划详情 sheet — 原型 planDetailSheet 的 React 化。
 *
 * 打开方式:openSheet("planDetail", { plan })  // plan: PlanItem
 *
 * 字段对齐原型:客户/标题 + 状态 pill + 计划时间 + 类型 + 计划内容。
 * 动作:
 *   - 填写拜访内容(visit 类型)→ visitSheet,预填客户
 *   - 标记完成 → PUT /plans/{id} status=done
 *   - 客户详情(有 customer_id)→ customerSheet
 *   - 删除 → DELETE /plans/{id}(用户显式点击 + confirm)
 */
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { api } from "../../lib/api";
import { fmtDateTime } from "../../lib/labels";
import { useSheetStore } from "../../store/sheets";
import type { PlanItem } from "../../types/api";
import { Sheet } from "../sheet/Sheet";

interface PlanDetailPayload {
  plan: PlanItem;
}

const STATUS_LABEL: Record<string, string> = {
  pending: "待办",
  done: "已完成",
  cancelled: "已取消",
};

export function PlanDetailSheet() {
  const payload = useSheetStore((s) => s.payload) as PlanDetailPayload | null;
  const openSheet = useSheetStore((s) => s.openSheet);
  const closeSheets = useSheetStore((s) => s.closeSheets);
  const queryClient = useQueryClient();
  const p = payload?.plan;

  const doneMut = useMutation({
    mutationFn: () => api.put<{ id: string }>(`/plans/${p!.id}`, { status: "done" }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["plans"] });
      closeSheets();
    },
  });

  const delMut = useMutation({
    mutationFn: () => api.del<void>(`/plans/${p!.id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["plans"] });
      closeSheets();
    },
  });

  return (
    <Sheet name="planDetail" title={p?.type === "visit" ? "拜访计划详情" : "计划详情"}>
      {p && (
        <>
          <div className="customer-detail-card">
            <div className="detail-title">
              <h3>{p.customer_name || p.title}</h3>
              <span className="level-pill">
                {STATUS_LABEL[p.status] ?? p.status}
              </span>
            </div>
            <div className="detail-grid">
              <div className="detail-field">
                <span>计划时间</span>
                <b>{fmtDateTime(p.scheduled_at)}</b>
              </div>
              <div className="detail-field">
                <span>类型</span>
                <b>
                  {p.is_personal
                    ? "个人提醒"
                    : p.type === "visit"
                    ? "客户拜访"
                    : "自定义"}
                </b>
              </div>
              {p.customer_name && (
                <div className="detail-field full">
                  <span>标题</span>
                  <b>{p.title}</b>
                </div>
              )}
              <div className="detail-field full">
                <span>内容</span>
                <b>{p.content || "—"}</b>
              </div>
            </div>
          </div>

          <div className="actions">
            {p.type === "visit" && p.customer_id && (
              <button
                type="button"
                className="chip primary"
                onClick={() =>
                  openSheet("visit", {
                    customer_id: p.customer_id,
                    customer_name: p.customer_name,
                  })
                }
              >
                填写拜访内容
              </button>
            )}
            {p.status === "pending" && (
              <button
                type="button"
                className="chip"
                onClick={() => doneMut.mutate()}
                disabled={doneMut.isPending}
              >
                {doneMut.isPending ? "处理中..." : "标记完成"}
              </button>
            )}
            {p.customer_id && (
              <button
                type="button"
                className="chip"
                onClick={() =>
                  openSheet("customer", { customer_id: p.customer_id })
                }
              >
                客户详情
              </button>
            )}
            <button
              type="button"
              className="chip"
              onClick={() => {
                if (window.confirm("确定删除这条计划?")) delMut.mutate();
              }}
              disabled={delMut.isPending}
              style={{ color: "var(--danger)" }}
            >
              {delMut.isPending ? "删除中..." : "删除"}
            </button>
          </div>
        </>
      )}
    </Sheet>
  );
}
