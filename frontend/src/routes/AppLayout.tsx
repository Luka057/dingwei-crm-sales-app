/**
 * 应用主布局:顶部用户信息条 + Outlet + 底部 4 tab。
 */
import { LogOut } from "lucide-react";
import { Outlet, useNavigate } from "react-router-dom";

import { BottomNav } from "../components/BottomNav";
import { useAuthStore } from "../store/auth";

import styles from "./AppLayout.module.css";

export function AppLayout() {
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const navigate = useNavigate();

  return (
    <div className={styles.shell}>
      <header className={styles.header}>
        <div className={styles.greeting}>
          <span className={styles.eyebrow}>欢迎</span>
          <span className={styles.name}>
            {user?.name}
            <small className={styles.role}>
              {user?.role === "manager" ? "主管" : "销售"}
            </small>
          </span>
        </div>
        <button
          className={styles.logoutBtn}
          onClick={() => {
            logout();
            navigate("/login", { replace: true });
          }}
        >
          <LogOut size={16} />
          退出
        </button>
      </header>

      <main className={styles.content}>
        <Outlet />
      </main>

      <BottomNav />
    </div>
  );
}
