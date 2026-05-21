/**
 * Auth store(Zustand + persist)。
 *
 * localStorage key:`dingwei-sales-auth`
 *
 * 字段:
 *   - token: JWT(后端 /auth/login 签发)
 *   - user: { id, username, name, role, manager_id }
 *
 * role 决定 Q1 决议:Manager 才渲染日历 tab 顶部「团队概览」卡。
 */

import { create } from "zustand";
import { persist } from "zustand/middleware";

export type UserRole = "sales" | "manager" | "boss";

export interface AuthUser {
  id: string;
  username: string;
  name: string;
  role: UserRole;
  manager_id: string | null;
}

interface AuthState {
  token: string | null;
  user: AuthUser | null;
  login: (token: string, user: AuthUser) => void;
  logout: () => void;
  isManager: () => boolean;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      token: null,
      user: null,
      login: (token, user) => set({ token, user }),
      logout: () => set({ token: null, user: null }),
      isManager: () => get().user?.role === "manager",
    }),
    {
      name: "dingwei-sales-auth",
    }
  )
);
