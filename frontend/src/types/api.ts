/**
 * API DTO 类型 — 手工镜像后端 Pydantic schemas。
 *
 * Phase 1A 末期会用 `npx openapi-typescript http://localhost:3000/api/v1/openapi.json -o src/types/api.d.ts`
 * 替换为自动生成,届时本文件改名 api.legacy.ts 留备。
 *
 * 当前手写版本只覆盖前端最小贯通用到的几个字段。
 */

export type UserRole = "sales" | "manager" | "boss";

export interface UserInfo {
  id: string;
  username: string;
  name: string;
  role: UserRole;
  manager_id: string | null;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  token: string;
  user: UserInfo;
}

// ── plan / calendar ─────────────────────────────────────────────

export type PlanType = "visit" | "custom";
export type PlanStatus = "pending" | "done" | "cancelled";

export interface PlanItem {
  id: string;
  type: PlanType;
  customer_id: string | null;
  customer_name: string | null;
  title: string;
  scheduled_at: string;
  status: PlanStatus;
  is_personal: boolean;
  content: string | null;
}

export interface CalendarDay {
  date: string; // YYYY-MM-DD
  items: PlanItem[];
}

export interface CalendarResponse {
  year: number;
  month: number;
  days: CalendarDay[];
}

// ── customer ────────────────────────────────────────────────────

export type CustomerLevel = "A" | "B" | "C";

export interface CustomerListItem {
  id: string;
  name: string;
  short_name: string | null;
  level: CustomerLevel;
  contact_name: string | null;
  phone: string | null;
  last_visit_at: string | null;
  is_overdue: boolean;
  tags: string[];
}

export interface OverdueSummary {
  count: number;
  items: CustomerListItem[];
}

// ── manager (Q1 决议:日历 tab 顶部「团队概览」卡数据源) ────────

export interface SubordinateRow {
  user_id: string;
  name: string;
  username: string;
  visits_this_week: number;
  overdue_customers: number;
}

export interface TeamSummary {
  team_visits_this_week: number;
  team_overdue_customers: number;
  pending_transfers: number;
  subordinates: SubordinateRow[];
}
