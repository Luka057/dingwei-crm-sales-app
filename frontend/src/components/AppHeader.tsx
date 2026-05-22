/**
 * 顶部头部 — 原型 `.top`(状态栏 + hero)的 React 化。
 *
 * 结构对齐原型:
 *   .top
 *     .status   假状态栏(时间 + 圆点)— 还原原型手机外观
 *     .hero
 *       .calendar-menu-btn  月历菜单(agenda 模式才显示,点开全屏月历 — #28 后接)
 *       div > .kicker "Dingwei CRM" + h1 年月
 *       .weather  天气(原型装饰)
 *       .tone-trigger  调色板 → toneSheet
 */
import { useNavigate } from "react-router-dom";

import { useSheetStore } from "../store/sheets";

const WEEKDAY = "日一二三四五六";

export function AppHeader() {
  const openSheet = useSheetStore((s) => s.openSheet);
  const navigate = useNavigate();
  const now = new Date();
  const hh = String(now.getHours()).padStart(2, "0");
  const mm = String(now.getMinutes()).padStart(2, "0");

  return (
    <div className="top">
      <div className="status">
        <span>
          {hh}:{mm}
        </span>
        <div className="dots">
          <span />
          <span />
          <span />
        </div>
      </div>
      <div className="hero">
        <button
          className="calendar-menu-btn"
          aria-label="打开月历"
          onClick={() => navigate("/app/calendar")}
        >
          <svg
            viewBox="0 0 24 24"
            stroke="currentColor"
            fill="none"
            strokeWidth={2}
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M4 7h16M4 12h16M4 17h12" />
          </svg>
        </button>
        <div>
          <div className="kicker">Dingwei CRM</div>
          <h1>
            <span className="year">{now.getFullYear()} 年</span>{" "}
            <span className="month">{now.getMonth() + 1} 月</span>
          </h1>
        </div>
        <div className="weather">
          <div>
            <strong>{now.getDate()}</strong>
            <span>周{WEEKDAY[now.getDay()]} · 适合外访</span>
          </div>
        </div>
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
      </div>
    </div>
  );
}
