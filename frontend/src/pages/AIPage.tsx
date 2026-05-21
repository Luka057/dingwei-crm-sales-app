/**
 * AI tab — 占位 + 简单 chat(调 stub)。
 *
 * Q6 决议:AI 找板完整 UI 应该在,本占位先放最小 chat,找板 sheet 留 Phase 1B。
 */
import { Send } from "lucide-react";
import { useState, type FormEvent } from "react";

import { api } from "../lib/api";

import styles from "./placeholder.module.css";

interface ChatResp {
  reply: string;
  cards: unknown[];
}

interface Msg {
  role: "user" | "ai";
  text: string;
}

export function AIPage() {
  const [msgs, setMsgs] = useState<Msg[]>([
    { role: "ai", text: "你好,我是 AI 助手(1A stub),问客户/拜访/样板/周报。" },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

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
      setMsgs((prev) => [...prev, { role: "ai", text: "出错了,稍后再试" }]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className={styles.page}>
      <h1>AI</h1>
      <p className={styles.subtitle}>客户问答 · 找板(stub)</p>

      <div className={styles.aiChat}>
        {msgs.map((m, i) => (
          <div
            key={i}
            className={`${styles.bubble} ${
              m.role === "user" ? styles.userBubble : styles.aiBubble
            }`}
          >
            {m.text}
          </div>
        ))}
      </div>

      <form className={styles.input} onSubmit={send}>
        <input
          placeholder="问客户、拜访、样板、周报..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
        />
        <button type="submit" disabled={loading || !input.trim()}>
          <Send size={14} />
        </button>
      </form>

      <p className={styles.note}>
        Phase 1B 接 DeepSeek + Function Calling;Phase 2 视觉模型上线后开 AI 找板。
      </p>
    </div>
  );
}
