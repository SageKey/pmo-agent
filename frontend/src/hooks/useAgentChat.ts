import { useCallback, useRef, useState } from "react";
import { getStoredShareKey } from "@/lib/api";

export type AgentMessageRole = "user" | "assistant";

export interface ToolCall {
  name: string;
  input: Record<string, unknown>;
  resultPreview?: string;
}

export interface AgentMessage {
  id: string;
  role: AgentMessageRole;
  content: string;
  toolCalls?: ToolCall[];
  streaming?: boolean;
}

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";

function uid(): string {
  return Math.random().toString(36).slice(2, 10);
}

export function useAgentChat() {
  const [messages, setMessages] = useState<AgentMessage[]>([]);
  const [streaming, setStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const reset = useCallback(() => {
    abortRef.current?.abort();
    setMessages([]);
    setError(null);
    setStreaming(false);
  }, []);

  const send = useCallback(
    async (prompt: string) => {
      if (!prompt.trim() || streaming) return;
      setError(null);

      const userMsg: AgentMessage = {
        id: uid(),
        role: "user",
        content: prompt.trim(),
      };
      const assistantMsg: AgentMessage = {
        id: uid(),
        role: "assistant",
        content: "",
        toolCalls: [],
        streaming: true,
      };
      setMessages((m) => [...m, userMsg, assistantMsg]);
      setStreaming(true);

      // Build history for the API (exclude the in-progress assistant msg)
      const history = [...messages, userMsg].map((m) => ({
        role: m.role,
        content: m.content,
      }));

      const controller = new AbortController();
      abortRef.current = controller;

      try {
        const headers: Record<string, string> = {
          "Content-Type": "application/json",
        };
        const shareKey = getStoredShareKey();
        if (shareKey) headers["X-Share-Key"] = shareKey;

        const res = await fetch(`${API_BASE}/agent/chat`, {
          method: "POST",
          headers,
          body: JSON.stringify({ messages: history }),
          signal: controller.signal,
        });

        if (!res.ok || !res.body) {
          throw new Error(`HTTP ${res.status}`);
        }

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        // Minimal SSE parser
        // eslint-disable-next-line no-constant-condition
        while (true) {
          const { value, done } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });

          // Each event is separated by a blank line
          let idx: number;
          while ((idx = buffer.indexOf("\n\n")) !== -1) {
            const raw = buffer.slice(0, idx);
            buffer = buffer.slice(idx + 2);
            if (!raw.trim()) continue;

            // Parse event/data lines
            let event = "message";
            let data = "";
            for (const line of raw.split("\n")) {
              if (line.startsWith("event:")) event = line.slice(6).trim();
              else if (line.startsWith("data:")) data += line.slice(5).trim();
            }

            let payload: any = {};
            try {
              payload = JSON.parse(data);
            } catch {
              /* ignore */
            }

            if (event === "text") {
              setMessages((m) => {
                const last = m[m.length - 1];
                if (!last || last.role !== "assistant") return m;
                return [
                  ...m.slice(0, -1),
                  { ...last, content: last.content + (payload.delta ?? "") },
                ];
              });
            } else if (event === "tool") {
              setMessages((m) => {
                const last = m[m.length - 1];
                if (!last || last.role !== "assistant") return m;
                return [
                  ...m.slice(0, -1),
                  {
                    ...last,
                    toolCalls: [
                      ...(last.toolCalls ?? []),
                      { name: payload.name, input: payload.input ?? {} },
                    ],
                  },
                ];
              });
            } else if (event === "result") {
              setMessages((m) => {
                const last = m[m.length - 1];
                if (!last || last.role !== "assistant") return m;
                const calls = last.toolCalls ?? [];
                const lastCallIdx = calls
                  .map((c, i) => ({ c, i }))
                  .reverse()
                  .find(({ c }) => c.name === payload.name && !c.resultPreview);
                if (!lastCallIdx) return m;
                const newCalls = [...calls];
                newCalls[lastCallIdx.i] = {
                  ...newCalls[lastCallIdx.i],
                  resultPreview: payload.result_preview,
                };
                return [...m.slice(0, -1), { ...last, toolCalls: newCalls }];
              });
            } else if (event === "error") {
              setError(payload.message ?? "Unknown error");
            } else if (event === "done") {
              setMessages((m) => {
                const last = m[m.length - 1];
                if (!last || last.role !== "assistant") return m;
                return [...m.slice(0, -1), { ...last, streaming: false }];
              });
            }
          }
        }
      } catch (e) {
        if ((e as Error).name !== "AbortError") {
          setError((e as Error).message);
        }
      } finally {
        setStreaming(false);
        setMessages((m) => {
          const last = m[m.length - 1];
          if (!last || last.role !== "assistant") return m;
          return [...m.slice(0, -1), { ...last, streaming: false }];
        });
      }
    },
    [messages, streaming],
  );

  return { messages, streaming, error, send, reset };
}

export async function fetchAgentTools(): Promise<{
  model: string;
  configured: boolean;
  tools: { name: string; description: string }[];
}> {
  const headers: Record<string, string> = {};
  const shareKey = getStoredShareKey();
  if (shareKey) headers["X-Share-Key"] = shareKey;
  const res = await fetch(`${API_BASE}/agent/tools`, { headers });
  if (!res.ok) {
    return { model: "", configured: false, tools: [] };
  }
  return res.json();
}
