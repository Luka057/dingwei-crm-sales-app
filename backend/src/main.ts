import cors from "cors";
import express from "express";
import { z } from "zod";

const app = express();
const port = Number(process.env.PORT || 3000);

app.use(cors());                         // 允许前端(5173)跨端口访问本后端(3000)
app.use(express.json({ limit: "12mb" })); // 自动把请求体的 JSON 解析成对象

/* ============================================================================
 * 鼎伟 CRM —— 本地 mock 后端（假数据，给前端打磨用，不是生产后端）
 *
 * ★ 接口契约（重要概念）★
 *   前端 src/types/api.ts 里声明了每份数据"长什么样"——字段名一律 snake_case
 *   （下划线命名，如 last_visit_at）。后端返回的字段名必须和它逐字一致，前端
 *   才读得到。这套"前后端事先约定好的数据长相"就叫【接口契约】。
 *
 *   旧版 mock 用了 camelCase（驼峰，如 lastVisitAt），和前端对不上 → 前端读不到
 *   last_visit_at / is_overdue / week_start 等字段，界面才显得"半空"。这一版全部
 *   改成 snake_case，把契约对齐。
 * ========================================================================== */

// 当前登录用户（mock：不校验密码，永远当成销售"张伟"登录）
const currentUser = {
  id: "u_sales_001",
  username: "zhangwei",
  name: "张伟",
  role: "sales" as const,
  manager_id: "u_mgr_001",
};

// —— "今天" + 超期判定（运行时算，不存字段）——
const NOW = new Date();
function daysSince(iso: string | null): number | null {
  if (!iso) return null; // 从没拜访过 → 没法算天数
  return Math.floor((NOW.getTime() - new Date(iso).getTime()) / 86_400_000);
}
// 超期阈值：A 类 14 天 / B 类 30 天 / C 类 60 天没拜访就算"超期"
const OVERDUE_DAYS: Record<string, number> = { A: 14, B: 30, C: 60 };
function isOverdue(level: string, lastVisitAt: string | null): boolean {
  const d = daysSince(lastVisitAt);
  return d !== null && d > (OVERDUE_DAYS[level] ?? 30);
}

/* ───────────────────────── 假数据：客户 ───────────────────────── */

interface CustomerSeed {
  id: string;
  name: string;
  short_name: string | null;
  level: "A" | "B" | "C";
  contact_name: string | null;
  contact_title: string | null;
  phone: string | null;
  address: string | null;
  last_visit_at: string | null;
  sample: boolean;     // 样板中
  this_week: boolean;  // 本周拜访
}

const customers: CustomerSeed[] = [
  { id: "c_hongyuan", name: "宏远服饰", short_name: "宏远", level: "A", contact_name: "李建国", contact_title: "采购总监", phone: "138****6271", address: "佛山南海区里水镇宏远工业园", last_visit_at: "2026-05-10T15:00:00+08:00", sample: true, this_week: false },
  { id: "c_jinhua", name: "锦华辅料", short_name: "锦华", level: "A", contact_name: "陈敏", contact_title: "经理", phone: "139****4118", address: "广州番禺区石基镇锦华工业区", last_visit_at: "2026-04-16T14:20:00+08:00", sample: false, this_week: false },
  { id: "c_hengjia", name: "恒嘉箱包", short_name: "恒嘉", level: "B", contact_name: "王芳", contact_title: "采购", phone: "136****9082", address: "东莞厚街镇恒嘉箱包园区", last_visit_at: "2026-05-30T11:00:00+08:00", sample: true, this_week: true },
  { id: "c_dongchen", name: "东晨制衣", short_name: "东晨", level: "A", contact_name: "刘强", contact_title: "老板", phone: "137****2255", address: "佛山顺德区均安镇东晨路 12 号", last_visit_at: "2026-05-28T10:00:00+08:00", sample: false, this_week: true },
  { id: "c_shengnan", name: "盛南鞋业", short_name: "盛南", level: "B", contact_name: "赵磊", contact_title: "生产主管", phone: "135****7733", address: "温州瓯海区盛南工业区", last_visit_at: "2026-04-20T16:30:00+08:00", sample: false, this_week: false },
  { id: "c_yucheng", name: "裕成宠物用品", short_name: "裕成", level: "C", contact_name: "孙丽", contact_title: "采购专员", phone: "133****1900", address: "金华义乌市裕成电商园", last_visit_at: "2026-02-20T09:30:00+08:00", sample: false, this_week: false },
  { id: "c_xinrui", name: "新锐户外", short_name: "新锐", level: "B", contact_name: "周伟", contact_title: "研发", phone: "131****8421", address: "宁波鄞州区新锐户外装备城", last_visit_at: null, sample: false, this_week: false },
];

// 客户 KPI（360 详情页用）。没列到的客户走 defaultKpis。
const customerKpis: Record<string, { visits: number; samples: number; orders: number; conversion_rate: number }> = {
  c_hongyuan: { visits: 9, samples: 3, orders: 1, conversion_rate: 0.33 },
  c_jinhua: { visits: 6, samples: 1, orders: 0, conversion_rate: 0 },
  c_hengjia: { visits: 4, samples: 2, orders: 1, conversion_rate: 0.5 },
  c_dongchen: { visits: 7, samples: 0, orders: 2, conversion_rate: 0.4 },
};
const defaultKpis = { visits: 0, samples: 0, orders: 0, conversion_rate: 0 };

// 把内部 seed 转成"客户列表项"——字段严格对齐前端 CustomerListItem
function toCustomerListItem(c: CustomerSeed) {
  const overdue = isOverdue(c.level, c.last_visit_at);
  const tags: string[] = [];
  if (overdue) tags.push("overdue");
  if (c.sample) tags.push("sample");
  if (c.this_week) tags.push("week");
  return {
    id: c.id,
    name: c.name,
    short_name: c.short_name,
    level: c.level,
    contact_name: c.contact_name,
    phone: c.phone,
    last_visit_at: c.last_visit_at,
    is_overdue: overdue,
    tags,
  };
}

/* ───────────────────────── 假数据：拜访记录 ───────────────────────── */

interface VisitSeed {
  id: string;
  customer_id: string;
  salesperson_id: string;
  visit_at: string;
  method: "offline" | "phone" | "wechat";
  intention: "good" | "likely_order" | "wait" | "none";
  target_person: string | null;
  target_title: string | null;
  content: string;
  next_follow_at: string | null;
  ai_summary: string | null;
  has_attachments: boolean;
}

const visitRecords: VisitSeed[] = [
  { id: "v_001", customer_id: "c_hongyuan", salesperson_id: currentUser.id, visit_at: "2026-05-10T15:00:00+08:00", method: "offline", intention: "likely_order", target_person: "李建国", target_title: "采购总监", content: "客户认可上次织带手感，但担心颜色批次稳定性，要求月底前再确认宽度调整样板。", next_follow_at: "2026-06-05T10:00:00+08:00", ai_summary: "客户认可手感，主要顾虑颜色批次稳定性；需重新确认宽度，月底有试单机会。", has_attachments: true },
  { id: "v_002", customer_id: "c_hongyuan", salesperson_id: currentUser.id, visit_at: "2026-04-18T10:00:00+08:00", method: "phone", intention: "wait", target_person: "李建国", target_title: "采购总监", content: "电话沟通新款松紧带需求，客户暂时观望，等下季度订单计划。", next_follow_at: null, ai_summary: null, has_attachments: false },
  { id: "v_003", customer_id: "c_jinhua", salesperson_id: currentUser.id, visit_at: "2026-04-16T14:20:00+08:00", method: "offline", intention: "good", target_person: "陈敏", target_title: "经理", content: "带新报价线下拜访，客户对价格敏感，希望主管确认最低报价空间后再定。", next_follow_at: "2026-06-04T14:00:00+08:00", ai_summary: "价格敏感，需主管确认报价底线后再跟进。", has_attachments: false },
  { id: "v_004", customer_id: "c_hengjia", salesperson_id: currentUser.id, visit_at: "2026-05-30T11:00:00+08:00", method: "wechat", intention: "likely_order", target_person: "王芳", target_title: "采购", content: "微信确认箱包织带样板，客户基本满意，准备小批量试单。", next_follow_at: "2026-06-06T09:00:00+08:00", ai_summary: "样板基本满意，准备小批量试单。", has_attachments: false },
];

// 把内部 seed 转成"拜访摘要"——对齐前端 VisitRecordSummary（注意 content_preview）
function toVisitSummary(v: VisitSeed) {
  return {
    id: v.id,
    visit_at: v.visit_at,
    method: v.method,
    intention: v.intention,
    target_person: v.target_person,
    content_preview: v.content.length > 40 ? v.content.slice(0, 40) + "…" : v.content,
    has_attachments: v.has_attachments,
    ai_summary: v.ai_summary,
  };
}

/* ───────────────────────── 假数据：日程/计划 ───────────────────────── */

interface Plan {
  id: string;
  type: "visit" | "custom";
  customer_id: string | null;
  customer_name: string | null;
  title: string;
  scheduled_at: string;
  status: "pending" | "done" | "cancelled";
  is_personal: boolean;
  content: string | null;
}

// 注意：日历按"当前月"取数，所以计划要铺在 2026-06（含今天 06-03）才看得到
const plans: Plan[] = [
  { id: "p_001", type: "visit", customer_id: "c_hongyuan", customer_name: "宏远服饰", title: "宏远服饰", scheduled_at: "2026-06-03T09:30:00+08:00", status: "pending", is_personal: false, content: "确认宽度调整样板反馈" },
  { id: "p_002", type: "visit", customer_id: "c_jinhua", customer_name: "锦华辅料", title: "锦华辅料", scheduled_at: "2026-06-03T14:30:00+08:00", status: "pending", is_personal: false, content: "带新报价线下拜访" },
  { id: "p_003", type: "custom", customer_id: null, customer_name: null, title: "整理本周拜访记录", scheduled_at: "2026-06-03T18:00:00+08:00", status: "pending", is_personal: true, content: "晚上整理今天两家客户的拜访要点" },
  { id: "p_004", type: "visit", customer_id: "c_hengjia", customer_name: "恒嘉箱包", title: "恒嘉箱包", scheduled_at: "2026-06-02T10:00:00+08:00", status: "done", is_personal: false, content: "微信确认样板，已完成" },
  { id: "p_005", type: "visit", customer_id: "c_dongchen", customer_name: "东晨制衣", title: "东晨制衣", scheduled_at: "2026-06-05T11:00:00+08:00", status: "pending", is_personal: false, content: "送样并谈下季度合作" },
  { id: "p_006", type: "custom", customer_id: null, customer_name: null, title: "准备月度客户分析", scheduled_at: "2026-06-06T15:00:00+08:00", status: "pending", is_personal: false, content: "汇总 A 类客户进展，给主管周会用" },
  { id: "p_007", type: "visit", customer_id: "c_shengnan", customer_name: "盛南鞋业", title: "盛南鞋业", scheduled_at: "2026-06-09T09:00:00+08:00", status: "pending", is_personal: false, content: "久未拜访，重新建立联系" },
];

/* ───────────────────────── 假数据：周报 ───────────────────────── */

interface WeeklyReport {
  id: string;
  salesperson_id: string;
  salesperson_name: string | null;
  week_start: string;
  summary: string | null;
  next_plan: string | null;
  notes: string | null;
  status: "draft" | "submitted" | "reopened";
  created_at: string;
  updated_at: string;
}

// 两份已提交的历史周报；本周还没有 → 前端会显示"未创建 / 开始录入"
const weeklyReports: WeeklyReport[] = [
  { id: "wr_2026_19", salesperson_id: currentUser.id, salesperson_name: currentUser.name, week_start: "2026-05-04", summary: "完成拜访 14 次，推进宏远、东晨两个重点客户。", next_plan: "确认宏远宽度调整样板，拜访锦华并提交新报价。", notes: "锦华对价格敏感，需要主管确认最低报价空间。", status: "submitted", created_at: "2026-05-09T18:00:00+08:00", updated_at: "2026-05-09T18:00:00+08:00" },
  { id: "wr_2026_20", salesperson_id: currentUser.id, salesperson_name: currentUser.name, week_start: "2026-05-11", summary: "完成拜访 11 次，恒嘉样板确认进入试单阶段。", next_plan: "跟进恒嘉试单，开发盛南鞋业新需求。", notes: "盛南久未联系，需尽快重新拜访。", status: "submitted", created_at: "2026-05-16T17:30:00+08:00", updated_at: "2026-05-16T17:30:00+08:00" },
];

/* ════════════════════════════ 接口（路由） ════════════════════════════ */

app.get("/api/v1/health", (_req, res) => {
  res.json({ ok: true, service: "dingwei-crm-sales-backend", time: new Date().toISOString() });
});

app.post("/api/v1/auth/login", (_req, res) => {
  // mock：不校验密码，直接发一个假 token + 当前用户
  res.json({ token: "mock-sales-token", user: currentUser });
});

// —— 日历：按 year+month 过滤计划，并按日期分组 ——
app.get("/api/v1/plans/calendar", (req, res) => {
  const year = String(req.query.year || "2026");
  const month = String(req.query.month || "6").padStart(2, "0");
  const monthPlans = plans.filter((p) => p.scheduled_at.startsWith(`${year}-${month}`));
  res.json({ year: Number(year), month: Number(month), days: groupPlansByDate(monthPlans) });
});

// —— 新建计划：请求体用 snake_case，和前端 PlanCreate 对齐 ——
app.post("/api/v1/plans", (req, res) => {
  const schema = z.object({
    type: z.enum(["visit", "custom"]),
    customer_id: z.string().nullable().optional(),
    title: z.string().min(1),
    scheduled_at: z.string(),
    content: z.string().nullable().optional(),
    is_personal: z.boolean().nullable().optional(),
  });
  const body = schema.parse(req.body);
  const cust = body.customer_id ? customers.find((c) => c.id === body.customer_id) : undefined;
  // is_personal：前端给了就用；没给则按"自定义且无客户=个人提醒"推断
  const is_personal = body.is_personal ?? (body.type === "custom" && !body.customer_id);
  const plan: Plan = {
    id: `p_${Date.now()}`,
    type: body.type,
    customer_id: body.customer_id ?? null,
    customer_name: cust?.name ?? null,
    title: body.title,
    scheduled_at: body.scheduled_at,
    status: "pending",
    is_personal,
    content: body.content ?? null,
  };
  plans.push(plan);
  res.status(201).json(plan);
});

app.put("/api/v1/plans/:id", (req, res) => {
  const plan = plans.find((item) => item.id === req.params.id);
  if (!plan) return res.status(404).json({ detail: "计划不存在" });
  Object.assign(plan, req.body); // 把请求体里的字段覆盖上去（如 status: "done"）
  res.json(plan);
});

app.delete("/api/v1/plans/:id", (req, res) => {
  const index = plans.findIndex((item) => item.id === req.params.id);
  if (index < 0) return res.status(404).json({ detail: "计划不存在" });
  res.json(plans.splice(index, 1)[0]);
});

// —— 客户列表（支持 keyword / level / overdue 过滤）——
app.get("/api/v1/customers", (req, res) => {
  const keyword = String(req.query.keyword || "");
  const level = String(req.query.level || "");
  const overdue = req.query.overdue === "true";
  const list = customers.map(toCustomerListItem).filter((c) => {
    if (keyword && !`${c.name}${c.contact_name ?? ""}`.includes(keyword)) return false;
    if (level && c.level !== level) return false;
    if (overdue && !c.is_overdue) return false;
    return true;
  });
  res.json(list);
});

// —— 超期汇总（日历页"建议跟进 / AI 今日建议"用）——
// ⚠️ 必须放在 "/customers/:id" 之前，否则 "overdue-summary" 会被当成某个客户 id
app.get("/api/v1/customers/overdue-summary", (_req, res) => {
  const items = customers.map(toCustomerListItem).filter((c) => c.is_overdue);
  res.json({ count: items.length, items });
});

// —— 客户 360 详情 ——
app.get("/api/v1/customers/:id", (req, res) => {
  const c = customers.find((item) => item.id === req.params.id);
  if (!c) return res.status(404).json({ detail: "客户不存在" });
  res.json({
    id: c.id,
    name: c.name,
    short_name: c.short_name,
    level: c.level,
    ai_score: null,
    status: "active",
    owner_id: currentUser.id,
    contact_name: c.contact_name,
    contact_title: c.contact_title,
    phone: c.phone,
    address: c.address,
    last_visit_at: c.last_visit_at,
    is_overdue: isOverdue(c.level, c.last_visit_at),
    created_at: "2025-09-01T09:00:00+08:00",
    kpis: customerKpis[c.id] ?? defaultKpis,
    visit_records: visitRecords.filter((v) => v.customer_id === c.id).map(toVisitSummary),
  });
});

// —— 录入拜访 ——
app.post("/api/v1/visit-records", (req, res) => {
  const record = { id: `v_${Date.now()}`, salesperson_id: currentUser.id, ...req.body };
  // 顺手把该客户的 last_visit_at 更新成本次拜访时间（让"超期"实时变化）
  const cust = customers.find((c) => c.id === req.body?.customer_id);
  if (cust && req.body?.visit_at) cust.last_visit_at = req.body.visit_at;
  res.status(201).json(record);
});

// —— 周报：列表 ——
app.get("/api/v1/weekly-reports", (_req, res) => {
  res.json(weeklyReports);
});

// —— 周报：新建（草稿或直接提交）——
app.post("/api/v1/weekly-reports", (req, res) => {
  const schema = z.object({
    week_start: z.string(),
    summary: z.string().nullable().optional(),
    next_plan: z.string().nullable().optional(),
    notes: z.string().nullable().optional(),
    status: z.enum(["draft", "submitted", "reopened"]).optional(),
  });
  const body = schema.parse(req.body);
  const nowIso = new Date().toISOString();
  const report: WeeklyReport = {
    id: `wr_${Date.now()}`,
    salesperson_id: currentUser.id,
    salesperson_name: currentUser.name,
    week_start: body.week_start,
    summary: body.summary ?? null,
    next_plan: body.next_plan ?? null,
    notes: body.notes ?? null,
    status: body.status ?? "draft",
    created_at: nowIso,
    updated_at: nowIso,
  };
  weeklyReports.unshift(report); // 放到最前面
  res.status(201).json(report);
});

// —— 周报：更新（继续填写 / 提交）——
app.put("/api/v1/weekly-reports/:id", (req, res) => {
  const report = weeklyReports.find((r) => r.id === req.params.id);
  if (!report) return res.status(404).json({ detail: "周报不存在" });
  Object.assign(report, req.body, { updated_at: new Date().toISOString() });
  res.json(report);
});

// —— 周报：AI 生成草稿（mock：返回固定文案）——
app.post("/api/v1/weekly-reports/generate-ai-draft", (_req, res) => {
  res.json({
    summary: "本周围绕 A 类客户和样板推进，完成 12 次拜访计划，重点推进宏远、锦华、恒嘉三个事项。",
    next_plan: "下周优先确认宏远样板反馈，线下拜访锦华辅料，补齐盛南鞋业新需求。",
    notes: "锦华对价格较敏感，宏远月底可能有试单机会。",
  });
});

// —— AI 助手（mock：固定回话；真模型 Phase 1B 接入）——
app.post("/api/v1/ai/chat", (req, res) => {
  const message = String(req.body?.message || "");
  const reply = message.includes("样板")
    ? "当前样板待确认客户：恒嘉箱包、宏远服饰。"
    : "本周建议优先跟进宏远服饰和锦华辅料两个 A 类客户（均已超期）。";
  res.json({ reply, cards: [] });
});

// —— AI 找板（同事的模块，先放 mock 占位）——
app.post("/api/v1/ai/board-search", (req, res) => {
  res.json({
    query: req.body,
    matches: [
      { sample_no: "HY-20-BK-软手感", score: 0.92, reason: "宽度、颜色、手感要求相似，关联宏远历史样板。" },
      { sample_no: "JH-18-BK-耐磨款", score: 0.84, reason: "与锦华辅料历史需求接近，可作为备选板样。" },
    ],
  });
});

// 把一组计划按"日期(YYYY-MM-DD)"分组 → [{ date, items }]
function groupPlansByDate(items: Plan[]) {
  const map = new Map<string, Plan[]>();
  for (const item of items) {
    const date = item.scheduled_at.slice(0, 10);
    map.set(date, [...(map.get(date) || []), item]);
  }
  // 按日期升序排好再返回
  return Array.from(map.entries())
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([date, items]) => ({ date, items }));
}

app.listen(port, () => {
  console.log(`Dingwei CRM sales backend listening on http://localhost:${port}`);
});
