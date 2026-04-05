import { useState } from "react";
import { motion } from "framer-motion";
import { Loader2, MessageSquare, Send, Trash2 } from "lucide-react";
import type { Comment } from "@/types/comment";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { avatarTone, initials, relativeDate, shortDate } from "@/lib/format";
import { useAddComment, useDeleteComment } from "@/hooks/useComments";
import { useDisplayName } from "@/hooks/useDisplayName";
import { cn } from "@/lib/cn";

export function CommentsPanel({
  projectId,
  comments,
}: {
  projectId: string;
  comments: Comment[];
}) {
  const [draft, setDraft] = useState("");
  const [name, setName] = useDisplayName();
  const addMutation = useAddComment(projectId);
  const deleteMutation = useDeleteComment(projectId);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const body = draft.trim();
    if (!body) return;
    try {
      await addMutation.mutateAsync({ author: name, body });
      setDraft("");
    } catch {
      /* error surfaces via addMutation.error */
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Discussion</CardTitle>
          <span className="text-xs text-slate-500">
            {comments.length} {comments.length === 1 ? "comment" : "comments"}
          </span>
        </div>
      </CardHeader>
      <CardContent>
        {/* Composer */}
        <form onSubmit={handleSubmit} className="mb-5 space-y-2">
          <div className="flex gap-2">
            <div
              className={cn(
                "flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-xs font-semibold",
                avatarTone(name),
              )}
              title={name}
            >
              {initials(name)}
            </div>
            <div className="flex-1 space-y-1.5">
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Your name"
                className="w-full rounded-md border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs text-slate-900 placeholder:text-slate-400 focus:border-navy-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-navy-100"
              />
              <div className="relative">
                <textarea
                  value={draft}
                  onChange={(e) => setDraft(e.target.value)}
                  placeholder="Add a comment, status update, or decision…"
                  rows={2}
                  className="w-full resize-none rounded-md border border-slate-200 bg-white px-3 py-2 pr-10 text-sm text-slate-900 placeholder:text-slate-400 focus:border-navy-400 focus:outline-none focus:ring-2 focus:ring-navy-100"
                  onKeyDown={(e) => {
                    if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
                      handleSubmit(e as unknown as React.FormEvent);
                    }
                  }}
                />
                <button
                  type="submit"
                  disabled={!draft.trim() || addMutation.isPending}
                  className="absolute bottom-2 right-2 flex h-6 w-6 items-center justify-center rounded text-slate-400 transition-colors hover:bg-slate-100 hover:text-navy-700 disabled:cursor-not-allowed disabled:opacity-30"
                  title="Post (⌘+Enter)"
                >
                  {addMutation.isPending ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  ) : (
                    <Send className="h-3.5 w-3.5" />
                  )}
                </button>
              </div>
              {addMutation.isError && (
                <div className="text-[11px] text-red-700">
                  Failed: {(addMutation.error as Error).message}
                </div>
              )}
            </div>
          </div>
        </form>

        {/* Thread */}
        {comments.length === 0 ? (
          <div className="flex flex-col items-center gap-3 py-8 text-center">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-slate-100 text-slate-400">
              <MessageSquare className="h-6 w-6" />
            </div>
            <div className="text-sm font-semibold text-slate-700">No comments yet</div>
            <div className="max-w-xs text-xs text-slate-500">
              Drop the first status update, question, or decision above.
            </div>
          </div>
        ) : (
          <ul className="space-y-5">
            {comments.map((c, i) => {
              const when = c.created_at ? relativeDate(c.created_at) : null;
              const isStatus = c.comment_type === "status_update";
              return (
                <motion.li
                  key={c.id}
                  initial={{ opacity: 0, y: 4 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.25, delay: i * 0.03 }}
                  className="group flex gap-3"
                >
                  <div
                    className={cn(
                      "flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-xs font-semibold",
                      avatarTone(c.author),
                    )}
                    title={c.author ?? ""}
                  >
                    {initials(c.author)}
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-baseline gap-2">
                      <span className="text-sm font-semibold text-slate-900">
                        {c.author ?? "System"}
                      </span>
                      {isStatus && (
                        <span className="rounded bg-sky-100 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-sky-700">
                          Status update
                        </span>
                      )}
                      {c.created_at && (
                        <span
                          className="text-[11px] text-slate-500"
                          title={shortDate(c.created_at)}
                        >
                          {when?.label ?? shortDate(c.created_at)}
                        </span>
                      )}
                      <button
                        onClick={() => {
                          if (confirm("Delete this comment?")) {
                            deleteMutation.mutate(c.id);
                          }
                        }}
                        disabled={deleteMutation.isPending}
                        className="ml-auto rounded p-1 text-slate-300 opacity-0 transition-all hover:bg-red-50 hover:text-red-600 group-hover:opacity-100"
                        title="Delete comment"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                    <div className="mt-1 whitespace-pre-wrap text-sm text-slate-700">
                      {c.body}
                    </div>
                  </div>
                </motion.li>
              );
            })}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
