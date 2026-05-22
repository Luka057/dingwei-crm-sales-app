/**
 * 底部 4 tab 导航 — 原型同款 SVG 图标 + 视觉。
 *
 * AGENT_HANDOFF §7:只 4 项,不增减。
 */
import { NavLink } from "react-router-dom";

const NavBtn = ({
  to,
  label,
  children,
}: {
  to: string;
  label: string;
  children: React.ReactNode;
}) => (
  <NavLink
    to={to}
    className={({ isActive }) => (isActive ? "active" : "")}
  >
    {children}
    <span>{label}</span>
  </NavLink>
);

export function BottomNav() {
  return (
    <nav className="nav">
      <NavBtn to="/app/calendar" label="日历">
        <svg viewBox="0 0 24 24">
          <path d="M8 2v4M16 2v4M3 10h18" />
          <rect x="3" y="4" width="18" height="18" rx="2" />
        </svg>
      </NavBtn>
      <NavBtn to="/app/customers" label="客户">
        <svg viewBox="0 0 24 24">
          <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
          <circle cx="9" cy="7" r="4" />
          <path d="M22 21v-2a4 4 0 0 0-3-3.87" />
          <path d="M16 3.13a4 4 0 0 1 0 7.75" />
        </svg>
      </NavBtn>
      <NavBtn to="/app/reports" label="周报">
        <svg viewBox="0 0 24 24">
          <path d="M4 19.5V5a2 2 0 0 1 2-2h11a3 3 0 0 1 3 3v15H6a2 2 0 0 1-2-2Z" />
          <path d="M8 7h6M8 11h8" />
        </svg>
      </NavBtn>
      <NavBtn to="/app/ai" label="AI">
        <svg viewBox="0 0 24 24">
          <path d="M12 3l1.7 5.3L19 10l-5.3 1.7L12 17l-1.7-5.3L5 10l5.3-1.7L12 3Z" />
        </svg>
      </NavBtn>
    </nav>
  );
}
