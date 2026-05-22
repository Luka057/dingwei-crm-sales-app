/**
 * 新增日程 sheet — 原型 planSheet 的 React 化。
 *
 * 字段对齐原型:
 *   - 日程类型 segmented:visit / custom
 *   - 标题 / 客户:用 <input list="..."> + <datalist>(原型只是普通 input,这里加客户名提示)
 *   - 时间:datetime-local
 *   - 内容:textarea
 *
 * Q8(决议)— is_personal toggle:
 *   只在 type=custom 时显示。默认勾上("个人提醒"),销售可关掉(变工作准备)。
 *   提交时,如果用户没选客户,后端推断 is_personal=True;前端 toggle 显式覆盖。
 *
 * 提交 → POST /plans → invalidate ["plans","calendar"] → 关闭。
 */
import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { ApiError, api } from "../../lib/api";
import { useSheetStore } from "../../store/sheets";
import type {
  CustomerListItem,
  PlanCreate,
  PlanType,
} from "../../types/api";
import { Sheet } from "../sheet/Sheet";

interface PlanSheetPayload {
  date?: string; // YYYY-MM-DD,从日历点 +FAB 时传入做时间预填
  customer_id?: string;
  customer_name?: string;
}

function nowLocalIso(date?: string): string {
  const d = date ? new Date(`${date}T09:00:00`) : new Date();
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(
    d.getHours()
  )}:${pad(d.getMinutes())}`;
}

export function PlanSheet() {
  const isActive = useSheetStore((s) => s.activeSheet === "plan");
  const payload = useSheetStore((s) => s.payload) as PlanSheetPayload | null;
  const closeSheets = useSheetStore((s) => s.closeSheets);
  const queryClient = useQueryClient();

  const [type, setType] = useState<PlanType>("visit");
  const [title, setTitle] = useState("");
  const [scheduledAt, setScheduledAt] = useState(nowLocalIso());
  const [content, setContent] = useState("");
  const [isPersonal, setIsPersonal] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 打开 sheet 时按 payload 预填 / 重置
  useEffect(() => {
    if (isActive) {
      setType(payload?.customer_name ? "visit" : "visit");
      setTitle(payload?.customer_name ?? "");
      setScheduledAt(nowLocalIso(payload?.date));
      setContent("");
      setIsPersonal(false);
      setError(null);
    }
  }, [isActive, payload]);

  // 客户列表(autocomplete + id lookup)
  const customersQ = useQuery({
    queryKey: ["customers", "all-for-picker"],
    queryFn: () => api.get<CustomerListItem[]>("/customers"),
    enabled: isActive,
    staleTime: 60_000,
  });

  const customerByName = (name: string): CustomerListItem | undefined =>
    customersQ.data?.find((c) => c.name === name.trim());

  const saveMut = useMutation({
    mutationFn: async () => {
      const customer = type === "visit" ? customerByName(title) : undefined;

      const body: PlanCreate = {
        type,
        customer_id: customer?.id ?? null,
        title: title.trim() || (customer?.name ?? "新计划"),
        scheduled_at: new Date(scheduledAt).toISOString(),
        content: content.trim() || null,
        is_personal: type === "custom" ? isPersonal : false,
      };

      if (type === "visit" && !customer) {
        throw new Error("拜访类型必须选已有客户(在标题里输入客户名,从下拉里选)");
      }

      return api.post<{ id: string }>("/plans", body);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["plans"] });
      closeSheets();
    },
    onError: (err) => {
      if (err instanceof ApiError) {
        setError(
          typeof err.detail === "string"
            ? err.detail
            : `保存失败:HTTP ${err.status}`
        );
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("保存失败,请重试");
      }
    },
  });

  return (
    <Sheet name="plan" title="新增日程">
      <div className="field">
        <label>日程类型</label>
        <div className="segmented two">
          <button
            type="button"
            className={"seg" + (type === "visit" ? " active" : "")}
            onClick={() => setType("visit")}
          >
            拜访
          </button>
          <button
            type="button"
            className={"seg" + (type === "custom" ? " active" : "")}
            onClick={() => setType("custom")}
          >
            自定义
          </button>
        </div>
      </div>

      <div className="field">
        <label>{type === "visit" ? "客户(必选)" : "标题"}</label>
        <input
          list="plan-sheet-customers"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder={
            type === "visit" ? "输入客户名,从下拉里选" : "例如:整理本周客户"
          }
        />
        {type === "visit" && (
          <datalist id="plan-sheet-customers">
            {customersQ.data?.map((c) => (
              <option key={c.id} value={c.name} />
            ))}
          </datalist>
        )}
      </div>

      <div className="field">
        <label>时间</label>
        <input
          type="datetime-local"
          value={scheduledAt}
          onChange={(e) => setScheduledAt(e.target.value)}
        />
      </div>

      <div className="field">
        <label>内容</label>
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="本次计划要点(可选)"
        />
      </div>

      {/* Q8: custom 类型 + 无客户时,显示 is_personal toggle */}
      {type === "custom" && (
        <div className="field">
          <label style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <input
              type="checkbox"
              checked={isPersonal}
              onChange={(e) => setIsPersonal(e.target.checked)}
            />
            <span>个人提醒(不汇总给主管)</span>
          </label>
        </div>
      )}

      {error && (
        <div
          style={{
            padding: "10px 14px",
            borderRadius: 10,
            background: "rgba(217,54,43,0.08)",
            color: "var(--danger)",
            fontSize: 13,
            fontWeight: 600,
            marginTop: 8,
          }}
        >
          {error}
        </div>
      )}

      <div className="actions">
        <button
          type="button"
          className="chip primary"
          onClick={() => saveMut.mutate()}
          disabled={saveMut.isPending || !title.trim()}
        >
          {saveMut.isPending ? "保存中..." : "保存到日历"}
        </button>
        <button type="button" className="chip" onClick={closeSheets}>
          取消
        </button>
      </div>
    </Sheet>
  );
}
