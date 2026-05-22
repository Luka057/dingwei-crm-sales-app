/* 鼎伟 CRM 前端 API 层 —— 在原型主 <script> 之前加载,提供全局 api / 登录 / helpers。
   设计:原型视觉代码不动,数据来源换成这里的真接口。 */
(function (global) {
  "use strict";
  const API_BASE = "/api/v1";
  const TOKEN_KEY = "dingwei-sales-token";
  const USER_KEY = "dingwei-sales-user";

  const getToken = () => localStorage.getItem(TOKEN_KEY);
  const setToken = (t) => localStorage.setItem(TOKEN_KEY, t);
  const clearToken = () => { localStorage.removeItem(TOKEN_KEY); localStorage.removeItem(USER_KEY); };
  const getUser = () => { try { return JSON.parse(localStorage.getItem(USER_KEY) || "null"); } catch { return null; } };

  // 统一请求:自动带 token;401 → 清 token + 弹登录;JSON 自动序列化
  async function apiFetch(path, opts) {
    opts = opts || {};
    const headers = Object.assign({}, opts.headers || {});
    const token = getToken();
    if (token) headers["Authorization"] = "Bearer " + token;
    let body = opts.body;
    if (body && !(body instanceof FormData)) {
      headers["Content-Type"] = "application/json";
      body = JSON.stringify(body);
    }
    const res = await fetch(API_BASE + path, { method: opts.method || "GET", headers, body });
    if (res.status === 401) { clearToken(); global.CRM_showLogin && global.CRM_showLogin(); throw new Error("unauthorized"); }
    if (!res.ok) { throw new Error(res.status + " " + (await res.text())); }
    if (res.status === 204) return null;
    const ct = res.headers.get("content-type") || "";
    return ct.includes("application/json") ? res.json() : res.text();
  }

  const api = {
    login: (username, password) =>
      fetch(API_BASE + "/auth/login", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      }).then((r) => (r.ok ? r.json() : Promise.reject(r.status))),
    // ⚠️ 后端集合路由带尾斜杠(已对实际 OpenAPI 核对):/customers/ /plans/(POST) /visit-records/ /weekly-reports/
    calendar: (y, m) => apiFetch(`/plans/calendar?year=${y}&month=${m}`),
    customers: (qs) => apiFetch("/customers/" + (qs ? "?" + qs : "")),
    customerDetail: (id) => apiFetch(`/customers/${id}`),
    overdueSummary: () => apiFetch("/customers/overdue-summary"),
    createPlan: (b) => apiFetch("/plans/", { method: "POST", body: b }),
    updatePlan: (id, b) => apiFetch(`/plans/${id}`, { method: "PUT", body: b }),
    deletePlan: (id) => apiFetch(`/plans/${id}`, { method: "DELETE" }),
    createVisit: (b) => apiFetch("/visit-records/", { method: "POST", body: b }),
    uploadPhoto: (file) => { const fd = new FormData(); fd.append("file", file); return apiFetch("/uploads/visit-photo", { method: "POST", body: fd }); },
    weeklyReports: () => apiFetch("/weekly-reports/"),
    createWeekly: (b) => apiFetch("/weekly-reports/", { method: "POST", body: b }),
    submitWeekly: (id) => apiFetch(`/weekly-reports/${id}/submit`, { method: "POST" }),
    aiDraft: () => apiFetch("/weekly-reports/generate-ai-draft", { method: "POST" }),
    aiChat: (message) => apiFetch("/ai/chat", { method: "POST", body: { message } }),
    aiBoardSearch: (b) => apiFetch("/ai/board-search", { method: "POST", body: b }),
  };

  // ── helpers(适配器 Task F2/F3 追加在文件后面)──
  const METHOD_CN = { offline: "线下", phone: "电话", wechat: "微信" };
  const INTENTION_CN = { good: "进展良好", likely_order: "下单有望", wait: "持平等待", none: "没有意向" };
  function daysSince(iso) {
    if (!iso) return "—";
    const diff = Math.floor((Date.now() - new Date(iso).getTime()) / 86400000);
    return diff >= 0 ? String(diff) : "0";
  }
  function isoLocalToBackend(s) {
    // 原型时间输入形如 "2026-05-14 15:30" → ISO "2026-05-14T15:30:00"
    const m = s.trim().match(/(\d{4})-(\d{1,2})-(\d{1,2})[ T](\d{1,2}):(\d{2})/);
    if (!m) return null;
    const [, y, mo, d, h, mi] = m;
    return `${y}-${mo.padStart(2,"0")}-${d.padStart(2,"0")}T${h.padStart(2,"0")}:${mi}:00`;
  }

  global.CRM = { api, getToken, setToken, clearToken, getUser, USER_KEY,
                 METHOD_CN, INTENTION_CN, daysSince, isoLocalToBackend };
})(window);
