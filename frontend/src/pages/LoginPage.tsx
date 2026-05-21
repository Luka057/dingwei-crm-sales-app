/**
 * 登录页 — /login(公开)。
 *
 * - 调 POST /api/v1/auth/login
 * - 成功 → 写 auth store → 跳 /app/calendar(或 from)
 * - 失败 → 显示 inline error(不暴露具体原因)
 */
import { useState, type FormEvent } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import { ApiError, api } from "../lib/api";
import { useAuthStore } from "../store/auth";
import type { LoginResponse } from "../types/api";

import styles from "./LoginPage.module.css";

interface LocationState {
  from?: string;
}

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const login = useAuthStore((s) => s.login);

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const resp = await api.post<LoginResponse>(
        "/auth/login",
        { username: username.trim(), password },
        { auth: false }
      );
      login(resp.token, resp.user);
      const from = (location.state as LocationState | null)?.from;
      navigate(from || "/app/calendar", { replace: true });
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        setError("用户名或密码错误");
      } else {
        setError("登录失败,请稍后重试");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className={styles.shell}>
      <div className={styles.card}>
        <p className={styles.eyebrow}>Dingwei CRM</p>
        <h1 className={styles.title}>业务人员端</h1>
        <p className={styles.subtitle}>销售 · 主管登录</p>

        <form className={styles.form} onSubmit={handleSubmit}>
          <label className={styles.field}>
            <span>用户名</span>
            <input
              type="text"
              autoComplete="username"
              placeholder="zhangwei / wangManager"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              autoFocus
            />
          </label>

          <label className={styles.field}>
            <span>密码</span>
            <input
              type="password"
              autoComplete="current-password"
              placeholder="123456(试点默认密码)"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </label>

          {error && <div className={styles.error}>{error}</div>}

          <button
            type="submit"
            className={styles.submit}
            disabled={loading || !username || !password}
          >
            {loading ? "登录中..." : "登录"}
          </button>
        </form>

        <p className={styles.hint}>
          试点账号:zhangwei / liuyang / chenmin(销售)/ wangManager(主管)
          <br />
          密码统一 <code>123456</code>
        </p>
      </div>
    </div>
  );
}
