/**
 * 主题 / 配色 sheet — 原型 toneSheet 的 React 化。
 *
 * 三组选项:
 *   1. 显示模式 light / dark
 *   2. 日程主题 agenda(日程优先)/ calendar(月历优先)
 *   3. 整体配色 8 个色调(warm 暖纸 / milkfoam 奶泡白 / vanillalinen 香草 / strawberrymilk 草莓 /
 *      ocean 蓝调 / forest 松绿 / grape 淡紫 / graphite 石墨)
 *
 * 选项点击 → useThemeStore setter → localStorage + <html data-*> + 重渲。
 */
import type { CSSProperties } from "react";
import { useNavigate } from "react-router-dom";

import { useAuthStore } from "../../store/auth";
import { useSheetStore } from "../../store/sheets";
import {
  type Appearance,
  type Tone,
  type ViewTheme,
  useThemeStore,
} from "../../store/theme";
import { Sheet } from "../sheet/Sheet";

const TONES: Array<{
  value: Tone;
  label: string;
  paper: string;
  accent: string;
}> = [
  { value: "warm", label: "暖纸原色", paper: "#f7f4ed", accent: "#ff5a49" },
  { value: "milkfoam", label: "奶泡白", paper: "#FAF6F1", accent: "#d9b8a6" },
  {
    value: "vanillalinen",
    label: "香草亚麻",
    paper: "#F2E6D8",
    accent: "#d1a57f",
  },
  {
    value: "strawberrymilk",
    label: "草莓牛奶",
    paper: "#F6C7CF",
    accent: "#df4d63",
  },
  { value: "ocean", label: "清爽蓝调", paper: "#eef6fb", accent: "#246fe8" },
  { value: "forest", label: "松绿色调", paper: "#f1f7f0", accent: "#2f9f76" },
  { value: "grape", label: "淡紫色调", paper: "#f7f2fb", accent: "#825ee8" },
  { value: "graphite", label: "石墨灰调", paper: "#f2f3f2", accent: "#151716" },
];

const APPEARANCES: Array<{ value: Appearance; label: string }> = [
  { value: "light", label: "浅色模式" },
  { value: "dark", label: "深色模式" },
];

const VIEW_THEMES: Array<{ value: ViewTheme; label: string }> = [
  { value: "agenda", label: "日程优先" },
  { value: "calendar", label: "月历优先" },
];

export function ToneSheet() {
  const tone = useThemeStore((s) => s.tone);
  const appearance = useThemeStore((s) => s.appearance);
  const viewTheme = useThemeStore((s) => s.viewTheme);
  const setTone = useThemeStore((s) => s.setTone);
  const setAppearance = useThemeStore((s) => s.setAppearance);
  const setViewTheme = useThemeStore((s) => s.setViewTheme);
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const closeSheets = useSheetStore((s) => s.closeSheets);
  const navigate = useNavigate();

  return (
    <Sheet name="tone" title="调整配色">
      <span className="sheet-label">显示模式</span>
      <div className="theme-choice">
        {APPEARANCES.map((a) => (
          <button
            key={a.value}
            className={"theme-option" + (appearance === a.value ? " active" : "")}
            onClick={() => setAppearance(a.value)}
          >
            <strong>{a.label}</strong>
          </button>
        ))}
      </div>

      <span className="sheet-label">日程主题</span>
      <div className="theme-choice">
        {VIEW_THEMES.map((v) => (
          <button
            key={v.value}
            className={"theme-option" + (viewTheme === v.value ? " active" : "")}
            onClick={() => setViewTheme(v.value)}
          >
            <strong>{v.label}</strong>
          </button>
        ))}
      </div>

      <span className="sheet-label">整体配色</span>
      <div className="tone-list">
        {TONES.map((t) => (
          <button
            key={t.value}
            className={"tone-option" + (tone === t.value ? " active" : "")}
            style={
              {
                "--tone-paper": t.paper,
                "--tone-accent": t.accent,
              } as CSSProperties
            }
            onClick={() => setTone(t.value)}
          >
            <span className="tone-dot" />
            <span>
              <b className="tone-name">{t.label}</b>
            </span>
            <span className="tone-check">已选</span>
          </button>
        ))}
      </div>

      <span className="sheet-label">账号</span>
      <div className="actions" style={{ marginTop: 8 }}>
        <button
          type="button"
          className="chip"
          onClick={() => {
            closeSheets();
            logout();
            navigate("/login", { replace: true });
          }}
          style={{ color: "var(--danger)" }}
        >
          退出登录{user?.name ? ` · ${user.name}` : ""}
        </button>
      </div>
    </Sheet>
  );
}
