/**
 * 主题 store(tone × appearance × view-theme)。
 *
 * localStorage key(与原型 HTML 对齐,三个独立 key):
 *   - dingwei-sales-tone:        warm / ocean / forest / grape / graphite / milkfoam / vanillalinen / strawberrymilk
 *   - dingwei-sales-appearance:  light / dark
 *   - dingwei-sales-view-theme:  agenda / calendar(日程优先 / 月历优先)
 *
 * setter 同步:
 *   1. 写 localStorage
 *   2. 改 <html data-tone="..." data-appearance="..." data-view-theme="...">
 *   3. 更新 Zustand state(组件重渲)
 */
import { create } from "zustand";

export type Tone =
  | "warm"
  | "ocean"
  | "forest"
  | "grape"
  | "graphite"
  | "milkfoam"
  | "vanillalinen"
  | "strawberrymilk";
export type Appearance = "light" | "dark";
export type ViewTheme = "agenda" | "calendar";

const TONE_KEY = "dingwei-sales-tone";
const APPEARANCE_KEY = "dingwei-sales-appearance";
const VIEW_KEY = "dingwei-sales-view-theme";

const VALID_TONES: Tone[] = [
  "warm",
  "ocean",
  "forest",
  "grape",
  "graphite",
  "milkfoam",
  "vanillalinen",
  "strawberrymilk",
];
const VALID_APPEARANCE: Appearance[] = ["light", "dark"];
const VALID_VIEW: ViewTheme[] = ["agenda", "calendar"];

function readEnum<T extends string>(key: string, valid: T[], fallback: T): T {
  if (typeof window === "undefined") return fallback;
  const v = window.localStorage.getItem(key);
  return v && (valid as string[]).includes(v) ? (v as T) : fallback;
}

function writeEnum(key: string, value: string): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(key, value);
}

function setHtmlAttr(name: string, value: string): void {
  if (typeof document === "undefined") return;
  document.documentElement.setAttribute(name, value);
}

interface ThemeState {
  tone: Tone;
  appearance: Appearance;
  viewTheme: ViewTheme;
  setTone: (t: Tone) => void;
  setAppearance: (a: Appearance) => void;
  setViewTheme: (v: ViewTheme) => void;
}

export const useThemeStore = create<ThemeState>((set) => ({
  tone: readEnum(TONE_KEY, VALID_TONES, "warm"),
  appearance: readEnum(APPEARANCE_KEY, VALID_APPEARANCE, "light"),
  viewTheme: readEnum(VIEW_KEY, VALID_VIEW, "agenda"),
  setTone: (tone) => {
    writeEnum(TONE_KEY, tone);
    setHtmlAttr("data-tone", tone);
    set({ tone });
  },
  setAppearance: (appearance) => {
    writeEnum(APPEARANCE_KEY, appearance);
    setHtmlAttr("data-appearance", appearance);
    set({ appearance });
  },
  setViewTheme: (viewTheme) => {
    writeEnum(VIEW_KEY, viewTheme);
    setHtmlAttr("data-view-theme", viewTheme);
    set({ viewTheme });
  },
}));

/** 启动时把当前 store 值同步到 <html>(避免首屏闪烁)。main.tsx 顶层调一次。 */
export function applyHtmlAttrs(): void {
  const s = useThemeStore.getState();
  setHtmlAttr("data-tone", s.tone);
  setHtmlAttr("data-appearance", s.appearance);
  setHtmlAttr("data-view-theme", s.viewTheme);
}
