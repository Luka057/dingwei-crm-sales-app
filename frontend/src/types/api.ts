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

// ── customer 360(GET /customers/{id})────────────────────────────

export interface CustomerKpis {
  visits: number;
  samples: number;
  orders: number;
  conversion_rate: number; // 0~1
}

export interface VisitRecordSummary {
  id: string;
  visit_at: string;
  method: VisitMethod;
  intention: VisitIntention;
  target_person: string | null;
  content_preview: string;
  has_attachments: boolean;
  ai_summary: string | null;
}

export interface CustomerDetail {
  id: string;
  name: string;
  short_name: string | null;
  level: CustomerLevel;
  ai_score: number | null;
  status: string;
  owner_id: string;
  contact_name: string | null;
  contact_title: string | null;
  phone: string | null;
  address: string | null;
  last_visit_at: string | null;
  is_overdue: boolean;
  created_at: string;
  kpis: CustomerKpis;
  visit_records: VisitRecordSummary[];
}

export interface PlanCreate {
  type: PlanType;
  customer_id?: string | null;
  title: string;
  scheduled_at: string; // ISO local datetime, e.g. "2026-05-14T15:30:00"
  content?: string | null;
  is_personal?: boolean | null; // Q8: 后端推断,前端 toggle 可改
}

// ── visit-record / upload ───────────────────────────────────────

export type VisitMethod = "offline" | "phone" | "wechat";
export type VisitIntention = "good" | "likely_order" | "wait" | "none";

export interface VisitPhotoUploadResponse {
  id: string; // attachment id,visit_attachment.id
  type: "photo";
  storage_path: string;
  file_size: number;
  mime_type: string;
  uploaded_at: string;
}

export interface VisitRecordCreate {
  customer_id: string;
  visit_at: string; // ISO datetime,拜访发生的时间;后端必填
  method: VisitMethod;
  intention: VisitIntention;
  target_person?: string | null; // 拜访对象姓名
  target_title?: string | null; // 拜访对象职位
  content: string;
  next_follow_at?: string | null; // ISO datetime,下次跟进时间
  attachment_ids?: string[];
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
