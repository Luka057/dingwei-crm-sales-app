/**
 * 主布局 — 原型布局思路:
 * <main> 容 page,nav 底部固定。
 * 顶部不放用户条(原型没),靠各 page 自带 page-title。
 * 右上角浮一个小退出按钮(原型没,但试点必须有 — 否则换号麻烦)。
 */
import { LogOut } from "lucide-react";
import { Outlet, useNavigate } from "react-router-dom";

import { BottomNav } from "../components/BottomNav";
import { useAuthStore } from "../store/auth";

export function AppLayout() {
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const navigate = useNavigate();

  return (
    <>
      <main>
        <Outlet />
      </main>
      <BottomNav />

      {/* 浮动退出 — 仅试点用,正式版可移除或合到 settings sheet */}
      <button
        onClick={() => {
          logout();
          navigate("/login", { replace: true });
        }}
        title={`${user?.name ?? ""} · 退出`}
        style={{
          position: "fixed",
          top: "max(env(safe-area-inset-top), 12px)",
          right: 12,
          zIndex: 60,
          width: 36,
          height: 36,
          borderRadius: 999,
          background: "var(--panel)",
          border: "1px solid var(--line)",
          display: "inline-flex",
          alignItems: "center",
          justifyContent: "center",
          color: "var(--muted)",
          boxShadow: "0 4px 12px rgba(0,0,0,.06)",
        }}
      >
        <LogOut size={16} />
      </button>
    </>
  );
}
