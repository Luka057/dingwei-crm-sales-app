/**
 * AI tab — 原型 .ai-chat 完整视觉。
 *
 * 结构(对齐 prototype aiPage.html):
 *   .ai-chat
 *     .ai-topbar       菜单(历史) + AI 名称 + 新对话/找板
 *     .ai-empty-space  欢迎区(无消息时)
 *     .chat-thread     消息列表
 *     .ai-composer     输入框 + 附件 + 语音 + 发送
 */
import { useRef, useState, type FormEvent } from "react";

import { api } from "../lib/api";
import { useAuthStore } from "../store/auth";

interface ChatResp {
  reply: string;
  cards: unknown[];
}

interface Msg {
  role: "user" | "ai";
  text: string;
}

export function AIPage() {
  const user = useAuthStore((s) => s.user);
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  async function send(e: FormEvent) {
    e.preventDefault();
    if (!input.trim() || loading) return;
    const userText = input.trim();
    setMsgs((prev) => [...prev, { role: "user", text: userText }]);
    setInput("");
    setLoading(true);
    try {
      const resp = await api.post<ChatResp>("/ai/chat", { message: userText });
      setMsgs((prev) => [...prev, { role: "ai", text: resp.reply }]);
    } catch {
      setMsgs((prev) => [
        ...prev,
        { role: "ai", text: "网络出错,稍后再试" },
      ]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  }

  const hasMsgs = msgs.length > 0;

  return (
    <div className="page active" id="aiPage">
      <div className="ai-chat">
        <div className="ai-topbar">
          <button className="ai-round" type="button" aria-label="历史会话">
            <svg viewBox="0 0 24 24">
              <path d="M4 7h16M4 12h16M4 17h12" />
            </svg>
          </button>
          <div className="ai-model">鼎伟 AI</div>
          <button className="ai-round" type="button" aria-label="AI 找板">
            <svg viewBox="0 0 24 24">
              <path d="M12 5v14M5 12h14" />
            </svg>
          </button>
        </div>

        {!hasMsgs && (
          <div className="ai-empty-space">
            <div style={{ textAlign: "center", color: "var(--muted)", padding: "40px 20px" }}>
              <h2 style={{ margin: "0 0 8px", color: "var(--ink)" }}>
                你好,{user?.name}
              </h2>
              <p style={{ margin: 0, fontSize: 14 }}>
                问客户、拜访、样板、周报。1A 是固定回话 stub,
                <br />
                Phase 1B 接入 DeepSeek + Function Calling。
              </p>
            </div>
          </div>
        )}

        {hasMsgs && (
          <div className="chat-thread">
            {msgs.map((m, i) => (
              <div
                key={i}
                className={`chat-msg ${m.role === "user" ? "from-user" : "from-ai"}`}
              >
                <div className="chat-bubble">{m.text}</div>
              </div>
            ))}
            {loading && (
              <div className="chat-msg from-ai">
                <div className="chat-bubble">...</div>
              </div>
            )}
          </div>
        )}

        <form className="ai-composer" onSubmit={send}>
          <input
            ref={inputRef}
            id="aiChatInput"
            placeholder="问客户、拜访、样板、周报..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
          />
          <div className="ai-composer-actions">
            <div className="ai-composer-left">
              <button
                className="ai-icon-action"
                type="button"
                aria-label="添加附件"
              >
                <svg viewBox="0 0 24 24">
                  <path d="M12 5v14M5 12h14" />
                </svg>
              </button>
            </div>
            <div className="ai-composer-right">
              <button
                className="ai-icon-action"
                type="button"
                aria-label="语音输入"
              >
                <svg viewBox="0 0 24 24">
                  <path d="M12 3a3 3 0 0 0-3 3v6a3 3 0 0 0 6 0V6a3 3 0 0 0-3-3Z" />
                  <path d="M19 10v2a7 7 0 0 1-14 0v-2M12 19v3" />
                </svg>
              </button>
              <button
                className="ai-icon-action send"
                type="submit"
                aria-label="发送"
                disabled={!input.trim() || loading}
              >
                <svg viewBox="0 0 24 24">
                  <path d="M22 2 11 13" />
                  <path d="m22 2-7 20-4-9-9-4 20-7Z" />
                </svg>
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
