import { useEffect, useRef, useState } from "react";
import { Navigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { Send, Sparkles, Wrench, RotateCw, AlertCircle, Loader2 } from "lucide-react";
import { TopBar } from "@/components/layout/TopBar";
import { Card } from "@/components/ui/card";
import {
  fetchAgentTools,
  useAgentChat,
  type AgentMessage,
  type ToolCall,
} from "@/hooks/useAgentChat";
import { useHealth } from "@/hooks/useHealth";
import { avatarTone, initials } from "@/lib/format";
import { cn } from "@/lib/cn";

const SUGGESTIONS = [
  "What's the status of our highest-priority projects?",
  "Which roles are at or near capacity?",
  "Can we take on a 400-hour project with 60% developer allocation?",
  "When will Alex Young be free?",
  "What changed since our last planning session?",
];

export function AIAssistant() {
  const health = useHealth();
  const { messages, streaming, error, send, reset } = useAgentChat();
  const [input, setInput] = useState("");
  const [agentMeta, setAgentMeta] = useState<{
    model: string;
    configured: boolean;
    toolCount: number;
  } | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchAgentTools()
      .then((d) =>
        setAgentMeta({
          model: d.model,
          configured: d.configured,
          toolCount: d.tools.length,
        }),
      )
      .catch(() => setAgentMeta({ model: "", configured: false, toolCount: 0 }));
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages, streaming]);

  const handleSubmit = (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!input.trim() || streaming) return;
    send(input);
    setInput("");
  };

  const showSuggestions = messages.length === 0;

  // Public deployments disable the agent entirely — redirect to Executive.
  // Done after all hooks so the rules-of-hooks check is satisfied.
  if (health.data?.public_mode) {
    return <Navigate to="/executive" replace />;
  }

  return (
    <>
      <TopBar
        title="AI Assistant"
        subtitle="Ask the PMO agent about capacity, priorities, and what-if scenarios."
      />
      <div className="flex h-[calc(100vh-140px)] flex-col gap-4 p-8">
        {!agentMeta?.configured && agentMeta && (
          <Card className="ring-1 ring-inset ring-amber-200">
            <div className="flex items-start gap-3 p-4">
              <AlertCircle className="h-5 w-5 shrink-0 text-amber-600" />
              <div>
                <div className="text-sm font-semibold text-amber-900">
                  Anthropic API key not configured
                </div>
                <div className="mt-1 text-xs text-amber-800">
                  Set <code className="rounded bg-amber-100 px-1">ANTHROPIC_API_KEY</code>{" "}
                  in the backend <code>.env</code> file to enable the agent. The chat UI
                  is fully functional and will stream the moment the key is present.
                </div>
              </div>
            </div>
          </Card>
        )}

        {/* Messages */}
        <div
          ref={scrollRef}
          className="flex-1 overflow-y-auto rounded-xl border border-slate-200 bg-white shadow-card"
        >
          {showSuggestions ? (
            <EmptyState
              onPick={(p) => {
                setInput(p);
                send(p);
              }}
              agentMeta={agentMeta}
            />
          ) : (
            <div className="space-y-6 p-6">
              <AnimatePresence initial={false}>
                {messages.map((m) => (
                  <MessageRow key={m.id} message={m} />
                ))}
              </AnimatePresence>
            </div>
          )}
        </div>

        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-2 text-xs text-red-800">
            {error}
          </div>
        )}

        {/* Composer */}
        <form onSubmit={handleSubmit} className="flex items-center gap-2">
          <div className="flex-1">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={
                streaming
                  ? "The agent is thinking…"
                  : "Ask about capacity, priorities, what-ifs…"
              }
              disabled={streaming || !agentMeta?.configured}
              className="w-full rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 placeholder:text-slate-400 focus:border-navy-400 focus:outline-none focus:ring-2 focus:ring-navy-100 disabled:bg-slate-50 disabled:text-slate-400"
            />
          </div>
          <button
            type="submit"
            disabled={streaming || !input.trim() || !agentMeta?.configured}
            className="flex h-11 w-11 items-center justify-center rounded-lg bg-navy-900 text-white transition-colors hover:bg-navy-800 disabled:cursor-not-allowed disabled:bg-slate-300"
          >
            {streaming ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </button>
          <button
            type="button"
            onClick={reset}
            disabled={messages.length === 0}
            className="flex h-11 w-11 items-center justify-center rounded-lg border border-slate-200 text-slate-500 transition-colors hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
            title="Clear conversation"
          >
            <RotateCw className="h-4 w-4" />
          </button>
        </form>
      </div>
    </>
  );
}

function MessageRow({ message }: { message: AgentMessage }) {
  const isUser = message.role === "user";
  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      className={cn("flex gap-3", isUser && "flex-row-reverse")}
    >
      <div
        className={cn(
          "flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-xs font-semibold",
          isUser ? avatarTone("user") : "bg-navy-900 text-white",
        )}
      >
        {isUser ? initials("You") : <Sparkles className="h-4 w-4" />}
      </div>
      <div className={cn("min-w-0 flex-1", isUser && "flex justify-end")}>
        <div
          className={cn(
            "inline-block max-w-[85%] rounded-2xl px-4 py-3",
            isUser
              ? "bg-navy-900 text-white"
              : "bg-slate-50 text-slate-900 ring-1 ring-inset ring-slate-200",
          )}
        >
          {message.content && (
            <div className="whitespace-pre-wrap text-sm leading-relaxed">
              {message.content}
              {message.streaming && <StreamingCursor />}
            </div>
          )}
          {message.toolCalls && message.toolCalls.length > 0 && (
            <div className={cn("space-y-1.5", message.content ? "mt-3" : "")}>
              {message.toolCalls.map((call, i) => (
                <ToolCallChip key={i} call={call} />
              ))}
            </div>
          )}
          {!message.content && !message.toolCalls?.length && message.streaming && (
            <StreamingCursor />
          )}
        </div>
      </div>
    </motion.div>
  );
}

function ToolCallChip({ call }: { call: ToolCall }) {
  const pending = !call.resultPreview;
  return (
    <div
      className={cn(
        "flex items-center gap-2 rounded-lg px-2.5 py-1.5 text-[11px] ring-1 ring-inset",
        pending
          ? "bg-sky-50 text-sky-800 ring-sky-200"
          : "bg-emerald-50 text-emerald-800 ring-emerald-200",
      )}
    >
      <Wrench
        className={cn("h-3 w-3 shrink-0", pending && "animate-pulse")}
      />
      <span className="font-semibold">{call.name}</span>
      {pending ? (
        <span className="text-sky-600">· running…</span>
      ) : (
        <span className="truncate font-mono text-[10px] text-emerald-700">
          ✓ complete
        </span>
      )}
    </div>
  );
}

function StreamingCursor() {
  return (
    <span className="ml-0.5 inline-block h-3 w-1 animate-pulse rounded-sm bg-current align-middle opacity-70" />
  );
}

function EmptyState({
  onPick,
  agentMeta,
}: {
  onPick: (prompt: string) => void;
  agentMeta: { model: string; configured: boolean; toolCount: number } | null;
}) {
  return (
    <div className="flex h-full flex-col items-center justify-center p-8 text-center">
      <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-navy-500 to-navy-900 text-white shadow-elev">
        <Sparkles className="h-7 w-7" />
      </div>
      <h2 className="mt-5 text-xl font-semibold tracking-tight text-slate-900">
        Ask the PMO agent anything
      </h2>
      <p className="mt-1 max-w-md text-sm text-slate-500">
        Grounded in your live portfolio, roster, and capacity data.{" "}
        {agentMeta && agentMeta.toolCount > 0 && (
          <span className="text-slate-600">
            {agentMeta.toolCount} tools available
            {agentMeta.model && ` · ${agentMeta.model}`}.
          </span>
        )}
      </p>
      <div className="mt-8 flex w-full max-w-2xl flex-col gap-2">
        {SUGGESTIONS.map((s) => (
          <button
            key={s}
            onClick={() => onPick(s)}
            disabled={!agentMeta?.configured}
            className="group rounded-lg border border-slate-200 bg-white px-4 py-3 text-left text-sm text-slate-700 transition-colors hover:border-navy-200 hover:bg-navy-50 hover:text-navy-900 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <span className="mr-2 text-slate-400 group-hover:text-navy-500">→</span>
            {s}
          </button>
        ))}
      </div>
    </div>
  );
}
