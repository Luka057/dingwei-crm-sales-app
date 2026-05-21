/**
 * 统一 fetch 客户端。
 *
 * - base: '/api/v1'(vite dev proxy → http://localhost:3000)
 * - 自动注入 Authorization: Bearer <token>(从 auth store 取)
 * - 401 自动 logout + 跳转 /login
 * - 4xx/5xx 抛 ApiError(.status / .detail)
 */

import { useAuthStore } from "../store/auth";

const BASE = "/api/v1";

export class ApiError extends Error {
  status: number;
  detail: unknown;
  constructor(status: number, detail: unknown, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

interface RequestOptions extends RequestInit {
  /** 是否自动注入 token,默认 true。/auth/login 等公开端点传 false。 */
  auth?: boolean;
}

async function request<T>(
  path: string,
  options: RequestOptions = {}
): Promise<T> {
  const { auth = true, headers, ...rest } = options;
  const finalHeaders: Record<string, string> = {
    "content-type": "application/json",
    ...((headers as Record<string, string>) || {}),
  };

  if (auth) {
    const token = useAuthStore.getState().token;
    if (token) {
      finalHeaders["authorization"] = `Bearer ${token}`;
    }
  }

  const resp = await fetch(`${BASE}${path}`, {
    ...rest,
    headers: finalHeaders,
  });

  if (resp.status === 401 && auth) {
    // token 失效 → 清空 + 跳转
    useAuthStore.getState().logout();
    // 软重定向:让 RequireAuth 重新计算并 navigate
    if (typeof window !== "undefined" && !window.location.pathname.startsWith("/login")) {
      window.location.href = "/login";
    }
  }

  const text = await resp.text();
  let body: unknown = undefined;
  try {
    body = text ? JSON.parse(text) : undefined;
  } catch {
    body = text;
  }

  if (!resp.ok) {
    const detail =
      typeof body === "object" && body !== null && "detail" in body
        ? (body as { detail: unknown }).detail
        : body;
    throw new ApiError(
      resp.status,
      detail,
      typeof detail === "string"
        ? detail
        : `Request failed: HTTP ${resp.status}`
    );
  }

  return body as T;
}

export const api = {
  get<T>(path: string, options?: RequestOptions): Promise<T> {
    return request<T>(path, { ...options, method: "GET" });
  },
  post<T>(path: string, body?: unknown, options?: RequestOptions): Promise<T> {
    return request<T>(path, {
      ...options,
      method: "POST",
      body: body ? JSON.stringify(body) : undefined,
    });
  },
  put<T>(path: string, body?: unknown, options?: RequestOptions): Promise<T> {
    return request<T>(path, {
      ...options,
      method: "PUT",
      body: body ? JSON.stringify(body) : undefined,
    });
  },
  del<T>(path: string, options?: RequestOptions): Promise<T> {
    return request<T>(path, { ...options, method: "DELETE" });
  },
};
