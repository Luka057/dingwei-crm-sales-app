/**
 * 底部 4 tab 导航。
 *
 * AGENT_HANDOFF §7:**不要恢复底部多余菜单,只保留 4 项**。
 * Manager 视图通过日历 tab 顶部「团队概览」卡片进入(Q1 决议)。
 */
import { Bot, CalendarDays, FileText, Users } from "lucide-react";
import { NavLink } from "react-router-dom";

import styles from "./BottomNav.module.css";

const TABS = [
  { to: "/app/calendar", label: "日历", icon: CalendarDays },
  { to: "/app/customers", label: "客户", icon: Users },
  { to: "/app/reports", label: "周报", icon: FileText },
  { to: "/app/ai", label: "AI", icon: Bot },
];

export function BottomNav() {
  return (
    <nav className={styles.nav}>
      {TABS.map(({ to, label, icon: Icon }) => (
        <NavLink
          key={to}
          to={to}
          className={({ isActive }) =>
            `${styles.item} ${isActive ? styles.active : ""}`
          }
        >
          <Icon size={22} />
          <span className={styles.label}>{label}</span>
        </NavLink>
      ))}
    </nav>
  );
}
