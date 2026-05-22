/**
 * 全屏暗色遮罩 — 任意 sheet 打开时显示。点击关闭全部 sheet。
 *
 * CSS 来自 prototype.css `.overlay` / `.overlay.open`。
 */
import { useSheetStore } from "../../store/sheets";

export function SheetOverlay() {
  const isOpen = useSheetStore((s) => s.activeSheet !== null);
  const closeSheets = useSheetStore((s) => s.closeSheets);

  return (
    <div
      className={"overlay" + (isOpen ? " open" : "")}
      onClick={closeSheets}
      aria-hidden={!isOpen}
    />
  );
}
