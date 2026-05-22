/**
 * 浮动 + 按钮 — 原型 `.fab` 的 React 化。
 *
 * Q32 上下文感知:
 *   - /app/calendar → 新增计划(打开 planSheet)
 *   - 其他 page  → 暂不显示(原型 JS 同样只在 calendar tab 显示 fab)
 *
 * 待 customers / reports tab 有合适 FAB 动作时再扩展。
 */
import { useLocation } from "react-router-dom";

import { useSheetStore } from "../store/sheets";

export function Fab() {
  const location = useLocation();
  const openSheet = useSheetStore((s) => s.openSheet);

  if (location.pathname !== "/app/calendar") return null;

  return (
    <button
      className="fab"
      onClick={() => openSheet("plan")}
      aria-label="新增拜访计划"
    >
      <svg
        viewBox="0 0 24 24"
        stroke="currentColor"
        fill="none"
        strokeWidth={2.4}
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d="M12 5v14M5 12h14" />
      </svg>
    </button>
  );
}
