/**
 * 拜访录入 sheet — 原型 visitSheet 的 React 化 + Q7 决议:照片上传完整可用。
 *
 * 字段对齐原型:
 *   - 客户:从客户列表选(input + datalist),必选
 *   - 拜访方式 segmented:phone / wechat / offline(对应后端 method)
 *   - 客户意向 segmented(4 选):good / likely_order / wait / none
 *   - 拜访内容 textarea
 *   - 下次跟进:datetime-local(可选)
 *   - 【Q7 新增】照片上传:多张,5MB/张,JPEG/PNG,本地预览
 *
 * 提交流程(原型没有上传逻辑,这里加上):
 *   1. 逐张 POST /uploads/visit-photo (multipart) 拿 attachment_id
 *   2. POST /visit-records body 含 attachment_ids[]
 *   3. invalidate ["customers", "calendar"](拜访影响 last_visit_at + plan 状态)
 */
import { useEffect, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { ApiError, api } from "../../lib/api";
import { useSheetStore } from "../../store/sheets";
import type {
  CustomerListItem,
  VisitIntention,
  VisitMethod,
  VisitPhotoUploadResponse,
  VisitRecordCreate,
} from "../../types/api";
import { Sheet } from "../sheet/Sheet";

interface VisitSheetPayload {
  customer_id?: string;
  customer_name?: string;
}

interface PhotoSlot {
  localId: string;
  file: File;
  preview: string; // ObjectURL
  status: "pending" | "uploading" | "done" | "failed";
  attachmentId?: string;
  errorMsg?: string;
}

const METHODS: Array<{ value: VisitMethod; label: string }> = [
  { value: "phone", label: "电话" },
  { value: "wechat", label: "微信" },
  { value: "offline", label: "线下" },
];

const INTENTIONS: Array<{ value: VisitIntention; label: string }> = [
  { value: "good", label: "进展良好" },
  { value: "likely_order", label: "下单有望" },
  { value: "wait", label: "持平等待" },
  { value: "none", label: "没有意向" },
];

const MAX_PHOTO_SIZE = 5 * 1024 * 1024; // 5MB,对齐后端

export function VisitSheet() {
  const isActive = useSheetStore((s) => s.activeSheet === "visit");
  const payload = useSheetStore((s) => s.payload) as VisitSheetPayload | null;
  const closeSheets = useSheetStore((s) => s.closeSheets);
  const queryClient = useQueryClient();

  const [customerName, setCustomerName] = useState("");
  const [method, setMethod] = useState<VisitMethod>("phone");
  const [intention, setIntention] = useState<VisitIntention>("good");
  const [content, setContent] = useState("");
  const [nextFollowUp, setNextFollowUp] = useState("");
  const [photos, setPhotos] = useState<PhotoSlot[]>([]);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // 打开 sheet 时按 payload 预填 / 重置
  useEffect(() => {
    if (isActive) {
      setCustomerName(payload?.customer_name ?? "");
      setMethod("phone");
      setIntention("good");
      setContent("");
      setNextFollowUp("");
      setPhotos([]);
      setError(null);
    }
  }, [isActive, payload]);

  // 关闭时释放 ObjectURL
  useEffect(() => {
    if (!isActive) {
      photos.forEach((p) => URL.revokeObjectURL(p.preview));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isActive]);

  // 客户列表
  const customersQ = useQuery({
    queryKey: ["customers", "all-for-picker"],
    queryFn: () => api.get<CustomerListItem[]>("/customers"),
    enabled: isActive,
    staleTime: 60_000,
  });

  function handlePickPhotos(e: React.ChangeEvent<HTMLInputElement>) {
    const files = Array.from(e.target.files ?? []);
    e.target.value = ""; // 允许重复选同一张

    const ok: PhotoSlot[] = [];
    const errs: string[] = [];
    for (const f of files) {
      if (!["image/jpeg", "image/png"].includes(f.type)) {
        errs.push(`${f.name}: 仅支持 JPEG / PNG`);
        continue;
      }
      if (f.size > MAX_PHOTO_SIZE) {
        errs.push(`${f.name}: 超过 5MB`);
        continue;
      }
      ok.push({
        localId: `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
        file: f,
        preview: URL.createObjectURL(f),
        status: "pending",
      });
    }
    if (errs.length) setError(errs.join("; "));
    if (ok.length) setPhotos((prev) => [...prev, ...ok]);
  }

  function removePhoto(localId: string) {
    setPhotos((prev) => {
      const p = prev.find((x) => x.localId === localId);
      if (p) URL.revokeObjectURL(p.preview);
      return prev.filter((x) => x.localId !== localId);
    });
  }

  async function uploadOne(slot: PhotoSlot): Promise<string> {
    const form = new FormData();
    form.append("file", slot.file);
    const resp = await api.postForm<VisitPhotoUploadResponse>(
      "/uploads/visit-photo",
      form
    );
    return resp.id;
  }

  const saveMut = useMutation({
    mutationFn: async () => {
      const customer = customersQ.data?.find(
        (c) => c.name === customerName.trim()
      );
      if (!customer) {
        throw new Error("请从下拉里选已有客户(必填)");
      }
      if (!content.trim()) {
        throw new Error("拜访内容必填");
      }

      // 1. 串行上传所有照片(也可以并行,试点稳定优先)
      const attachmentIds: string[] = [];
      for (const slot of photos) {
        if (slot.attachmentId) {
          attachmentIds.push(slot.attachmentId);
          continue;
        }
        setPhotos((prev) =>
          prev.map((x) =>
            x.localId === slot.localId ? { ...x, status: "uploading" } : x
          )
        );
        try {
          const aid = await uploadOne(slot);
          attachmentIds.push(aid);
          setPhotos((prev) =>
            prev.map((x) =>
              x.localId === slot.localId
                ? { ...x, status: "done", attachmentId: aid }
                : x
            )
          );
        } catch (err) {
          const msg =
            err instanceof ApiError
              ? typeof err.detail === "string"
                ? err.detail
                : `HTTP ${err.status}`
              : err instanceof Error
              ? err.message
              : "上传失败";
          setPhotos((prev) =>
            prev.map((x) =>
              x.localId === slot.localId
                ? { ...x, status: "failed", errorMsg: msg }
                : x
            )
          );
          throw new Error(`照片上传失败:${msg}`);
        }
      }

      // 2. 创建拜访记录(visit_at = 此刻,实际拜访时间)
      const body: VisitRecordCreate = {
        customer_id: customer.id,
        visit_at: new Date().toISOString(),
        method,
        intention,
        content: content.trim(),
        next_follow_at: nextFollowUp
          ? new Date(nextFollowUp).toISOString()
          : null,
        attachment_ids: attachmentIds,
      };
      return api.post<{ id: string }>("/visit-records", body);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["customers"] });
      queryClient.invalidateQueries({ queryKey: ["plans"] });
      closeSheets();
    },
    onError: (err) => {
      setError(err instanceof Error ? err.message : "保存失败,请重试");
    },
  });

  return (
    <Sheet name="visit" title="填写拜访内容">
      <div className="field">
        <label>客户</label>
        <input
          list="visit-sheet-customers"
          value={customerName}
          onChange={(e) => setCustomerName(e.target.value)}
          placeholder="输入客户名,从下拉里选"
        />
        <datalist id="visit-sheet-customers">
          {customersQ.data?.map((c) => (
            <option key={c.id} value={c.name} />
          ))}
        </datalist>
      </div>

      <div className="field">
        <label>拜访方式</label>
        <div className="segmented">
          {METHODS.map((m) => (
            <button
              key={m.value}
              type="button"
              className={"seg" + (method === m.value ? " active" : "")}
              onClick={() => setMethod(m.value)}
            >
              {m.label}
            </button>
          ))}
        </div>
      </div>

      <div className="field">
        <label>客户意向</label>
        <div className="segmented four">
          {INTENTIONS.map((i) => (
            <button
              key={i.value}
              type="button"
              className={"seg" + (intention === i.value ? " active" : "")}
              onClick={() => setIntention(i.value)}
            >
              {i.label}
            </button>
          ))}
        </div>
      </div>

      <div className="field">
        <label>拜访内容</label>
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="客户反馈、关键事项、后续动作..."
        />
      </div>

      <div className="field">
        <label>下次跟进(可选)</label>
        <input
          type="datetime-local"
          value={nextFollowUp}
          onChange={(e) => setNextFollowUp(e.target.value)}
        />
      </div>

      {/* Q7 决议:照片上传 — 5MB / JPEG·PNG / 多张 */}
      <div className="field">
        <label>现场照片(可选,5MB/张,JPEG·PNG)</label>
        <input
          ref={fileInputRef}
          type="file"
          accept="image/jpeg,image/png"
          multiple
          onChange={handlePickPhotos}
          style={{ display: "none" }}
        />
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
          {photos.map((p) => (
            <div
              key={p.localId}
              style={{
                position: "relative",
                width: 72,
                height: 72,
                borderRadius: 12,
                overflow: "hidden",
                border: "1px solid var(--line)",
                background: "var(--subtle)",
              }}
            >
              <img
                src={p.preview}
                alt=""
                style={{ width: "100%", height: "100%", objectFit: "cover" }}
              />
              {p.status === "uploading" && (
                <div
                  style={{
                    position: "absolute",
                    inset: 0,
                    background: "rgba(0,0,0,.45)",
                    color: "#fff",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontSize: 11,
                  }}
                >
                  上传中
                </div>
              )}
              {p.status === "failed" && (
                <div
                  style={{
                    position: "absolute",
                    inset: 0,
                    background: "rgba(217,54,43,.6)",
                    color: "#fff",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontSize: 11,
                  }}
                >
                  失败
                </div>
              )}
              <button
                type="button"
                onClick={() => removePhoto(p.localId)}
                style={{
                  position: "absolute",
                  top: 2,
                  right: 2,
                  width: 20,
                  height: 20,
                  borderRadius: 999,
                  background: "rgba(0,0,0,.55)",
                  color: "#fff",
                  fontSize: 12,
                  lineHeight: 1,
                  border: "none",
                }}
                aria-label="删除"
              >
                ×
              </button>
            </div>
          ))}
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            style={{
              width: 72,
              height: 72,
              borderRadius: 12,
              border: "1.5px dashed var(--line)",
              background: "var(--soft)",
              color: "var(--muted)",
              fontSize: 24,
              lineHeight: 1,
            }}
            aria-label="添加照片"
          >
            +
          </button>
        </div>
      </div>

      {error && (
        <div
          style={{
            padding: "10px 14px",
            borderRadius: 10,
            background: "rgba(217,54,43,0.08)",
            color: "var(--danger)",
            fontSize: 13,
            fontWeight: 600,
            marginTop: 8,
          }}
        >
          {error}
        </div>
      )}

      <div className="actions">
        <button
          type="button"
          className="chip primary"
          onClick={() => saveMut.mutate()}
          disabled={saveMut.isPending || !customerName.trim() || !content.trim()}
        >
          {saveMut.isPending ? "保存中..." : "保存拜访"}
        </button>
        <button type="button" className="chip" onClick={closeSheets}>
          取消
        </button>
      </div>
    </Sheet>
  );
}
