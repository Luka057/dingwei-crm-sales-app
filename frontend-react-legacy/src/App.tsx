/**
 * 路由表(react-router-dom v7)。
 *
 * - /login                          → 登录(公开)
 * - /prototype                      → 原型 iframe(公开,设计参考)
 * - /app/*                          → RequireAuth
 *     - /app/calendar               → 日历(Sales/Manager 都看到自己 plan)
 *     - /app/customers              → 客户列表(支持 ?overdue=true)
 *     - /app/reports                → 周报列表
 *     - /app/ai                     → AI(chat + 找板)
 *     - /app/manager/team-summary   → 主管视图子页(Q1 决议)
 * - /                               → /app/calendar 重定向
 */
import { Navigate, Route, Routes } from "react-router-dom";

import { AppLayout } from "./routes/AppLayout";
import { RequireAuth } from "./routes/RequireAuth";

import { AIPage } from "./pages/AIPage";
import { CalendarPage } from "./pages/CalendarPage";
import { CustomersPage } from "./pages/CustomersPage";
import { LoginPage } from "./pages/LoginPage";
import { PrototypePage } from "./pages/PrototypePage";
import { ReportsPage } from "./pages/ReportsPage";
import { TeamSummaryPage } from "./pages/manager/TeamSummaryPage";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/prototype" element={<PrototypePage />} />

      <Route element={<RequireAuth />}>
        <Route path="/app" element={<AppLayout />}>
          <Route index element={<Navigate to="/app/calendar" replace />} />
          <Route path="calendar" element={<CalendarPage />} />
          <Route path="customers" element={<CustomersPage />} />
          <Route path="reports" element={<ReportsPage />} />
          <Route path="ai" element={<AIPage />} />
          <Route path="manager/team-summary" element={<TeamSummaryPage />} />
        </Route>
      </Route>

      <Route path="/" element={<Navigate to="/app/calendar" replace />} />
      <Route path="*" element={<Navigate to="/app/calendar" replace />} />
    </Routes>
  );
}
