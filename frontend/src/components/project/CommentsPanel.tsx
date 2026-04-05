import { motion } from "framer-motion";
import { MessageSquare } from "lucide-react";
import type { Comment } from "@/types/comment";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { avatarTone, initials, relativeDate, shortDate } from "@/lib/format";
import { cn } from "@/lib/cn";

export function CommentsPanel({ comments }: { comments: Comment[] }) {
  if (comments.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Discussion</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center gap-3 py-10 text-center">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-slate-100 text-slate-400">
              <MessageSquare className="h-6 w-6" />
            </div>
            <div className="text-sm font-semibold text-slate-700">No comments yet</div>
            <div className="max-w-xs text-xs text-slate-500">
              PMs can drop status updates, questions, or decisions here so the team
              has a durable record.
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

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
        <ul className="space-y-5">
          {comments.map((c, i) => {
            const when = c.created_at ? relativeDate(c.created_at) : null;
            const isStatus = c.comment_type === "status_update";
            return (
              <motion.li
                key={c.id}
                initial={{ opacity: 0, y: 4 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: i * 0.04 }}
                className="flex gap-3"
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
                  </div>
                  <div className="mt-1 whitespace-pre-wrap text-sm text-slate-700">
                    {c.body}
                  </div>
                </div>
              </motion.li>
            );
          })}
        </ul>
      </CardContent>
    </Card>
  );
}
