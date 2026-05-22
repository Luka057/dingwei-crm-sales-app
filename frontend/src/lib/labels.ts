/**
 * 枚举值 → 中文标签映射(前端展示用)。
 * 与原型 UI 文案对齐。
 */
import type { VisitIntention, VisitMethod } from "../types/api";

export const METHOD_LABEL: Record<VisitMethod, string> = {
  phone: "电话",
  wechat: "微信",
  offline: "线下",
};

export const INTENTION_LABEL: Record<VisitIntention, string> = {
  good: "进展良好",
  likely_order: "下单有望",
  wait: "持平等待",
  none: "没有意向",
};

export function fmtDateTime(iso: string): string {
  const d = new Date(iso);
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(
    d.getDate()
  )} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

export function fmtDate(iso: string): string {
  const d = new Date(iso);
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

export function daysSince(iso: string | null): number | null {
  if (!iso) return null;
  return Math.floor((Date.now() - new Date(iso).getTime()) / 86400000);
}
