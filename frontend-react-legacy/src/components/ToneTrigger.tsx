/**
 * 调色板触发按钮 — 原型 `.tone-trigger` 的 React 化。
 * 点击打开 toneSheet。
 *
 * 原型里它在 .screen-head 右侧(每个 page 顶部都有)。
 * Phase 1A 暂时放在 AppLayout 浮动位置;待 screen-head 抽出公共组件后,
 * 移到 screen-head 内。
 */
import { useSheetStore } from "../store/sheets";

export function ToneTrigger() {
  const openSheet = useSheetStore((s) => s.openSheet);
  return (
    <button
      className="tone-trigger"
      onClick={() => openSheet("tone")}
      aria-label="调整配色"
    >
      <svg
        viewBox="0 0 24 24"
        stroke="currentColor"
        fill="none"
        strokeWidth={2}
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d="M12 22a8 8 0 0 1 0-16h1.5a2.5 2.5 0 0 0 0-5H12a11 11 0 0 0 0 22Z" />
        <circle cx="7.5" cy="12" r=".8" />
        <circle cx="10.5" cy="8.5" r=".8" />
        <circle cx="10.5" cy="15.5" r=".8" />
      </svg>
    </button>
  );
}
