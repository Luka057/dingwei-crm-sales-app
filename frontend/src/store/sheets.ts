/**
 * Sheet 状态管理(Zustand)。
 *
 * 原型 HTML 用 .overlay + .sheet.open class 切换显示。这里抽到 React 状态:
 *   - activeSheet: 当前打开的 sheet 名(null = 没开)
 *   - payload:    可选数据(例如打开 planDetail 时把 plan 对象塞进来)
 *
 * 仅一个 sheet 同时打开(原型 closeSheets 行为)。打开新的会替代旧的。
 */
import { create } from "zustand";

export type SheetName =
  | "tone"
  | "plan"
  | "planDetail"
  | "eventEdit"
  | "visit"
  | "visitDetail"
  | "customer"
  | "reportForm"
  | "reportDetail"
  | "week"
  | "search"
  | "ai"
  | "boardSearch";

interface SheetState {
  activeSheet: SheetName | null;
  payload: unknown;
  openSheet: (name: SheetName, payload?: unknown) => void;
  closeSheets: () => void;
}

export const useSheetStore = create<SheetState>((set) => ({
  activeSheet: null,
  payload: null,
  openSheet: (name, payload = null) => set({ activeSheet: name, payload }),
  closeSheets: () => set({ activeSheet: null, payload: null }),
}));
