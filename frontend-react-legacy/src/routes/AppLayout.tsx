/**
 * 主布局 — 1:1 还原原型外壳结构:
 *
 *   <div class="phone calendar-mode [agenda-theme]">   手机外壳(居中/边框/背景)
 *     <div class="app-scroll">                          滚动容器
 *       <AppHeader/>  (.top: 状态栏 + hero 品牌/天气/调色)
 *       <main><Outlet/></main>
 *     </div>
 *     <Fab/> <BottomNav/>                                外壳内浮层
 *     <SheetOverlay/> + 各 sheet                         全屏 sheet 系统
 *   </div>
 *
 * view-theme(agenda/calendar)驱动 .phone 上的 .agenda-theme class
 * (原型 CSS 用 .phone.agenda-theme,不是 [data-view-theme])。
 */
import { AppHeader } from "../components/AppHeader";
import { BottomNav } from "../components/BottomNav";
import { Fab } from "../components/Fab";
import { Outlet } from "react-router-dom";

import { SheetOverlay } from "../components/sheet/SheetOverlay";
import { CustomerSheet } from "../components/sheets/CustomerSheet";
import { PlanDetailSheet } from "../components/sheets/PlanDetailSheet";
import { PlanSheet } from "../components/sheets/PlanSheet";
import { ToneSheet } from "../components/sheets/ToneSheet";
import { VisitDetailSheet } from "../components/sheets/VisitDetailSheet";
import { VisitSheet } from "../components/sheets/VisitSheet";
import { useThemeStore } from "../store/theme";

export function AppLayout() {
  const viewTheme = useThemeStore((s) => s.viewTheme);

  return (
    <div
      className={`phone calendar-mode${
        viewTheme === "agenda" ? " agenda-theme" : ""
      }`}
    >
      <div className="app-scroll">
        <AppHeader />
        <main>
          <Outlet />
        </main>
      </div>

      <Fab />
      <BottomNav />

      {/* Sheet 系统 — overlay 全屏暗罩 + 各 sheet 始终在 DOM,.open 控制可见 */}
      <SheetOverlay />
      <ToneSheet />
      <PlanSheet />
      <VisitSheet />
      <CustomerSheet />
      <VisitDetailSheet />
      <PlanDetailSheet />
      {/* TODO: 其余 6 个 sheet(report 系列 / week / search / ai / boardSearch / eventEdit)逐步移入 */}
    </div>
  );
}
