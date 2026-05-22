/**
 * 登录页 — /login(公开)。
 *
 * 视觉沿用原型主题变量,但本页不是原型的一部分(原型 demo 默认已登录),
 * 所以用内联样式 + CSS 变量,不依赖 prototype.css 的具体 class。
 */
import { useState, type FormEvent } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import { ApiError, api } from "../lib/api";
import { useAuthStore } from "../store/auth";
import type { LoginResponse } from "../types/api";

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
    <div
      style={{
        minHeight: "100vh",
        background: "var(--body-bg)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: 20,
      }}
    >
      <div
        style={{
          width: "min(420px, 100%)",
          background: "var(--panel-strong)",
          borderRadius: 24,
          padding: "36px 28px 28px",
          boxShadow: "var(--shadow)",
          border: "1px solid var(--line)",
        }}
      >
        <p
          style={{
            margin: 0,
            color: "var(--coral)",
            fontWeight: 800,
            letterSpacing: "0.1em",
            textTransform: "uppercase",
            fontSize: 12,
          }}
        >
          Dingwei CRM
        </p>
        <h1
          style={{
            margin: "6px 0 4px",
            fontSize: 32,
            color: "var(--ink)",
            fontWeight: 800,
          }}
        >
          业务人员端
        </h1>
        <p style={{ margin: "0 0 28px", color: "var(--muted)", fontSize: 14 }}>
          销售 · 主管登录
        </p>

        <form
          onSubmit={handleSubmit}
          style={{ display: "flex", flexDirection: "column", gap: 16 }}
        >
          <Field
            label="用户名"
            value={username}
            onChange={setUsername}
            placeholder="zhangwei / wangManager"
            autoComplete="username"
            autoFocus
          />
          <Field
            label="密码"
            value={password}
            onChange={setPassword}
            placeholder="123456(试点默认)"
            type="password"
            autoComplete="current-password"
          />

          {error && (
            <div
              style={{
                padding: "10px 14px",
                borderRadius: 10,
                background: "rgba(217,54,43,0.08)",
                color: "var(--danger)",
                fontSize: 13,
                fontWeight: 600,
              }}
            >
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading || !username || !password}
            style={{
              padding: "15px 16px",
              borderRadius: 14,
              background: "var(--coral)",
              color: "#fff",
              fontSize: 16,
              fontWeight: 700,
              opacity: loading || !username || !password ? 0.5 : 1,
            }}
          >
            {loading ? "登录中..." : "登录"}
          </button>
        </form>

        <p
          style={{
            margin: "24px 0 0",
            padding: "14px 16px",
            borderRadius: 12,
            background: "var(--subtle)",
            color: "var(--muted)",
            fontSize: 12,
            lineHeight: 1.6,
            border: "1px dashed var(--line)",
          }}
        >
          试点账号:zhangwei / liuyang / chenmin(销售)/ wangManager(主管)
          <br />
          密码统一{" "}
          <code
            style={{
              background: "var(--panel)",
              padding: "1px 6px",
              borderRadius: 4,
              fontFamily: "ui-monospace, monospace",
              color: "var(--ink)",
            }}
          >
            123456
          </code>
        </p>
      </div>
    </div>
  );
}

function Field({
  label,
  value,
  onChange,
  placeholder,
  type = "text",
  autoComplete,
  autoFocus,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder: string;
  type?: string;
  autoComplete?: string;
  autoFocus?: boolean;
}) {
  return (
    <label style={{ display: "flex", flexDirection: "column", gap: 8 }}>
      <span
        style={{
          fontSize: 13,
          color: "var(--muted)",
          fontWeight: 600,
        }}
      >
        {label}
      </span>
      <input
        type={type}
        autoComplete={autoComplete}
        autoFocus={autoFocus}
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        required
        style={{
          padding: "14px 16px",
          border: "1.5px solid var(--line)",
          borderRadius: 14,
          background: "var(--soft)",
          fontSize: 16,
          color: "var(--ink)",
          outline: "none",
        }}
      />
    </label>
  );
}
