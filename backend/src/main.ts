import cors from "cors";
import express from "express";
import { z } from "zod";

const app = express();
const port = Number(process.env.PORT || 3000);

app.use(cors());
app.use(express.json({ limit: "12mb" }));

type Plan = {
  id: string;
  type: "visit" | "custom";
  customerId?: string;
  title: string;
  scheduledAt: string;
  status: "pending" | "done" | "cancelled";
  content?: string;
};

const currentUser = { id: "u_sales_001", username: "zhangwei", name: "张伟", role: "sales" };

const customers = [
  {
    id: "c_hongyuan",
    name: "宏远服饰",
    level: "A",
    ownerId: currentUser.id,
    contact: "李总",
    phone: "138****6271",
    address: "佛山南海区里水镇宏远工业园",
    lastVisitAt: "2026-04-16T15:00:00+08:00",
    tags: ["overdue", "sample"]
  },
  {
    id: "c_jinhua",
    name: "锦华辅料",
    level: "A",
    ownerId: currentUser.id,
    contact: "陈经理",
    phone: "139****4118",
    address: "广州番禺区石基镇锦华工业区",
    lastVisitAt: "2026-04-13T14:20:00+08:00",
    tags: ["overdue"]
  },
  {
    id: "c_hengjia",
    name: "恒嘉箱包",
    level: "B",
    ownerId: currentUser.id,
    contact: "王小姐",
    phone: "136****9082",
    address: "东莞厚街镇恒嘉箱包园区",
    lastVisitAt: "2026-05-08T11:00:00+08:00",
    tags: ["sample", "week"]
  }
];

const plans: Plan[] = [
  {
    id: "p_001",
    type: "visit",
    customerId: "c_hongyuan",
    title: "宏远服饰",
    scheduledAt: "2026-05-14T09:30:00+08:00",
    status: "pending",
    content: "确认宽度调整样板反馈"
  },
  {
    id: "p_002",
    type: "visit",
    customerId: "c_jinhua",
    title: "锦华辅料",
    scheduledAt: "2026-05-14T14:30:00+08:00",
    status: "pending",
    content: "带新报价线下拜访"
  }
];

const visitRecords = [
  {
    id: "v_001",
    customerId: "c_hongyuan",
    salespersonId: currentUser.id,
    visitAt: "2026-05-14T09:30:00+08:00",
    method: "phone",
    intention: "likely_order",
    targetPerson: "李总",
    content: "客户认可上次织带手感，但担心颜色批次稳定性。",
    aiSummary: "客户认可手感，主要顾虑颜色批次稳定性；本周需重新确认宽度，月底有试单机会。"
  }
];

const weeklyReports = [
  {
    id: "wr_2026_19",
    weekStart: "2026-05-04",
    status: "submitted",
    summary: "完成拜访 14 次，推进宏远、东晨两个重点客户。",
    nextPlan: "确认宏远宽度调整样板，拜访锦华并提交新报价。",
    notes: "锦华对价格敏感，需要主管确认最低报价空间。",
    attachments: ["报价单.xlsx", "拜访照片 2 张"]
  }
];

app.get("/api/v1/health", (_req, res) => {
  res.json({ ok: true, service: "dingwei-crm-sales-backend", time: new Date().toISOString() });
});

app.post("/api/v1/auth/login", (_req, res) => {
  res.json({ token: "mock-sales-token", user: currentUser });
});

app.get("/api/v1/plans/calendar", (req, res) => {
  const year = String(req.query.year || "2026");
  const month = String(req.query.month || "5").padStart(2, "0");
  const monthPlans = plans.filter((plan) => plan.scheduledAt.startsWith(`${year}-${month}`));
  res.json({ year: Number(year), month: Number(month), days: groupPlansByDate(monthPlans) });
});

app.post("/api/v1/plans", (req, res) => {
  const schema = z.object({
    type: z.enum(["visit", "custom"]),
    customerId: z.string().optional(),
    title: z.string().min(1),
    scheduledAt: z.string(),
    content: z.string().optional()
  });
  const body = schema.parse(req.body);
  const plan: Plan = { id: `p_${Date.now()}`, status: "pending", ...body };
  plans.push(plan);
  res.status(201).json(plan);
});

app.put("/api/v1/plans/:id", (req, res) => {
  const plan = plans.find((item) => item.id === req.params.id);
  if (!plan) return res.status(404).json({ message: "Plan not found" });
  Object.assign(plan, req.body);
  res.json(plan);
});

app.delete("/api/v1/plans/:id", (req, res) => {
  const index = plans.findIndex((item) => item.id === req.params.id);
  if (index < 0) return res.status(404).json({ message: "Plan not found" });
  res.json(plans.splice(index, 1)[0]);
});

app.get("/api/v1/customers", (req, res) => {
  const keyword = String(req.query.keyword || "");
  const level = String(req.query.level || "");
  const overdue = req.query.overdue === "true";
  res.json(customers.filter((customer) => {
    if (keyword && !`${customer.name}${customer.contact}${customer.address}`.includes(keyword)) return false;
    if (level && customer.level !== level) return false;
    if (overdue && !customer.tags.includes("overdue")) return false;
    return true;
  }));
});

app.get("/api/v1/customers/:id", (req, res) => {
  const customer = customers.find((item) => item.id === req.params.id);
  if (!customer) return res.status(404).json({ message: "Customer not found" });
  res.json({
    ...customer,
    kpis: { visits: 9, samples: 3, orders: 1, conversionRate: 0.33 },
    visitRecords: visitRecords.filter((record) => record.customerId === customer.id)
  });
});

app.post("/api/v1/visit-records", (req, res) => {
  const record = { id: `v_${Date.now()}`, salespersonId: currentUser.id, ...req.body };
  visitRecords.push(record);
  res.status(201).json(record);
});

app.get("/api/v1/weekly-reports", (_req, res) => {
  res.json(weeklyReports);
});

app.post("/api/v1/weekly-reports/generate-ai-draft", (_req, res) => {
  res.json({
    summary: "本周围绕 A 类客户和样板推进完成 12 次拜访计划，重点推进宏远、锦华、恒嘉三个事项。",
    nextPlan: "下周优先确认宏远样板反馈，线下拜访锦华辅料，补齐东晨制衣新采购联系方式。",
    notes: "锦华对价格较敏感，宏远月底可能有试单机会。",
    attachments: ["本周拜访摘要.pdf"]
  });
});

app.post("/api/v1/ai/chat", (req, res) => {
  const message = String(req.body?.message || "");
  const reply = message.includes("样板")
    ? "当前样板待确认客户：恒嘉箱包、宏远服饰、盛南服饰。"
    : "本周建议优先跟进宏远服饰和锦华辅料两个 A 类客户。";
  res.json({ reply, cards: [] });
});

app.post("/api/v1/ai/board-search", (req, res) => {
  res.json({
    query: req.body,
    matches: [
      { sampleNo: "HY-20-BK-软手感", score: 0.92, reason: "宽度、颜色、手感要求相似，关联宏远历史样板。" },
      { sampleNo: "JH-18-BK-耐磨款", score: 0.84, reason: "与锦华辅料历史需求接近，可作为备选板样。" }
    ]
  });
});

function groupPlansByDate(items: typeof plans) {
  const map = new Map<string, typeof plans>();
  for (const item of items) {
    const date = item.scheduledAt.slice(0, 10);
    map.set(date, [...(map.get(date) || []), item]);
  }
  return Array.from(map.entries()).map(([date, items]) => ({ date, items }));
}

app.listen(port, () => {
  console.log(`Dingwei CRM sales backend listening on http://localhost:${port}`);
});
