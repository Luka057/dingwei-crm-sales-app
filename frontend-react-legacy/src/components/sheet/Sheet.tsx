/**
 * 通用 Sheet 容器 — 原型 `<section class="sheet" id="xxxSheet">` 的 React 化。
 *
 * 用法:
 *   <Sheet name="tone" title="调整配色">
 *     ...sheet body...
 *   </Sheet>
 *
 * .open class 由 useSheetStore.activeSheet 控制(CSS transform 动画)。
 * 头部带 grab handle + 标题 + 关闭按钮(对齐原型)。
 */
import type { ReactNode } from "react";

import { type SheetName, useSheetStore } from "../../store/sheets";

interface SheetProps {
  name: SheetName;
  title: string;
  children: ReactNode;
}

export function Sheet({ name, title, children }: SheetProps) {
  const isActive = useSheetStore((s) => s.activeSheet === name);
  const closeSheets = useSheetStore((s) => s.closeSheets);

  return (
    <section
      className={"sheet" + (isActive ? " open" : "")}
      id={`${name}Sheet`}
      aria-hidden={!isActive}
    >
      <div className="grab" />
      <div className="sheet-head">
        <h2>{title}</h2>
        <button className="icon-btn" onClick={closeSheets} aria-label="关闭">
          <svg
            viewBox="0 0 24 24"
            stroke="currentColor"
            fill="none"
            strokeWidth={2}
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M18 6 6 18M6 6l12 12" />
          </svg>
        </button>
      </div>
      {children}
    </section>
  );
}
