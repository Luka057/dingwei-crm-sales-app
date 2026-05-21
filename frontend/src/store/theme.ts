/**
 * 主题 store(tone × appearance × view-theme)。
 *
 * 引用:`docs/agent/AGENT_HANDOFF.md` §5 主题和本地状态
 *
 * localStorage keys(与原型 HTML 对齐):
 *   - dingwei-sales-tone:        warm / ocean / forest / grape / graphite / milkfoam / vanillalinen / strawberrymilk
 *   - dingwei-sales-appearance:  light / dark
 *   - dingwei-sales-view-theme:  agenda / calendar(日历优先 / 月历优先)
 *
 * 1A 仅做变量层,不开切换 UI(方案 1A.6 / Q1A 决议)。
 * 但 store 已就位,Phase 1B 可直接接 UI。
 */

import { useEffect } from "react";

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

function readEnum<T extends string>(
  key: string,
  valid: T[],
  fallback: T
): T {
  if (typeof window === "undefined") return fallback;
  const v = window.localStorage.getItem(key);
  return v && (valid as string[]).includes(v) ? (v as T) : fallback;
}

export function getCurrentTone(): Tone {
  return readEnum(TONE_KEY, VALID_TONES, "warm");
}

export function getCurrentAppearance(): Appearance {
  return readEnum(APPEARANCE_KEY, VALID_APPEARANCE, "light");
}

export function getCurrentViewTheme(): ViewTheme {
  return readEnum(VIEW_KEY, VALID_VIEW, "agenda");
}

/** 应用到 <html data-tone="..." data-appearance="..."> */
export function applyHtmlAttrs(): void {
  if (typeof document === "undefined") return;
  document.documentElement.setAttribute("data-tone", getCurrentTone());
  document.documentElement.setAttribute(
    "data-appearance",
    getCurrentAppearance()
  );
}

/** 启动时 hook(在 main.tsx 顶层调一次) */
export function useThemeBootstrap(): void {
  useEffect(() => {
    applyHtmlAttrs();
  }, []);
}
