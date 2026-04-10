import { useEffect } from "react";
import { useEditor, EditorContent } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import { Bold, Italic, List, ListOrdered, Heading2, Undo, Redo } from "lucide-react";
import { cn } from "@/lib/cn";

/**
 * Minimal WYSIWYG rich text editor wrapping TipTap.
 *
 * Emits HTML via `onChange`. Accepts HTML via `value`. The editor is
 * uncontrolled internally — we only sync `value` → editor when the
 * external value changes from something other than our own emit.
 *
 * Used for task notes (formerly called "description" pre-v7).
 */
export function RichTextEditor({
  value,
  onChange,
  minHeight = 140,
}: {
  value: string;
  onChange: (html: string) => void;
  minHeight?: number;
}) {
  const editor = useEditor({
    extensions: [StarterKit],
    content: value || "",
    editorProps: {
      attributes: {
        class: cn(
          "max-w-none text-sm text-slate-800 focus:outline-none",
          // List + heading + inline-formatting styles (Tailwind doesn't
          // add these by default — typography plugin would, but we
          // don't want to add another dependency)
          "[&_ul]:my-2 [&_ul]:list-disc [&_ul]:pl-6",
          "[&_ol]:my-2 [&_ol]:list-decimal [&_ol]:pl-6",
          "[&_li]:my-0.5",
          "[&_h1]:my-2 [&_h1]:text-2xl [&_h1]:font-bold",
          "[&_h2]:my-2 [&_h2]:text-xl [&_h2]:font-bold",
          "[&_h3]:my-1.5 [&_h3]:text-base [&_h3]:font-semibold",
          "[&_p]:my-1",
          "[&_strong]:font-bold",
          "[&_em]:italic",
          "[&_blockquote]:border-l-2 [&_blockquote]:border-slate-300 [&_blockquote]:pl-3 [&_blockquote]:italic [&_blockquote]:text-slate-600",
          "[&_code]:rounded [&_code]:bg-slate-100 [&_code]:px-1 [&_code]:py-0.5 [&_code]:font-mono [&_code]:text-xs",
        ),
        style: `min-height: ${minHeight}px;`,
      },
    },
    onUpdate: ({ editor }) => {
      onChange(editor.getHTML());
    },
  });

  // Sync external value changes (e.g., loading a different task)
  useEffect(() => {
    if (!editor) return;
    const currentHtml = editor.getHTML();
    // Only reset if the value actually differs — prevents caret jumps
    // when the parent re-renders mid-typing
    if (value !== currentHtml) {
      editor.commands.setContent(value || "");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value, editor]);

  if (!editor) {
    return (
      <div
        className="w-full rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-400"
        style={{ minHeight }}
      >
        Loading editor…
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-md border border-slate-200 bg-white focus-within:border-navy-400 focus-within:ring-2 focus-within:ring-navy-100">
      {/* Toolbar */}
      <div className="flex items-center gap-1 border-b border-slate-200 bg-slate-50 px-2 py-1">
        <ToolbarButton
          onClick={() => editor.chain().focus().toggleBold().run()}
          active={editor.isActive("bold")}
          title="Bold (Cmd+B)"
        >
          <Bold className="h-3.5 w-3.5" />
        </ToolbarButton>
        <ToolbarButton
          onClick={() => editor.chain().focus().toggleItalic().run()}
          active={editor.isActive("italic")}
          title="Italic (Cmd+I)"
        >
          <Italic className="h-3.5 w-3.5" />
        </ToolbarButton>
        <ToolbarButton
          onClick={() =>
            editor.chain().focus().toggleHeading({ level: 2 }).run()
          }
          active={editor.isActive("heading", { level: 2 })}
          title="Heading"
        >
          <Heading2 className="h-3.5 w-3.5" />
        </ToolbarButton>
        <div className="mx-1 h-4 w-px bg-slate-200" />
        <ToolbarButton
          onClick={() => editor.chain().focus().toggleBulletList().run()}
          active={editor.isActive("bulletList")}
          title="Bullet list"
        >
          <List className="h-3.5 w-3.5" />
        </ToolbarButton>
        <ToolbarButton
          onClick={() => editor.chain().focus().toggleOrderedList().run()}
          active={editor.isActive("orderedList")}
          title="Numbered list"
        >
          <ListOrdered className="h-3.5 w-3.5" />
        </ToolbarButton>
        <div className="mx-1 h-4 w-px bg-slate-200" />
        <ToolbarButton
          onClick={() => editor.chain().focus().undo().run()}
          disabled={!editor.can().undo()}
          title="Undo (Cmd+Z)"
        >
          <Undo className="h-3.5 w-3.5" />
        </ToolbarButton>
        <ToolbarButton
          onClick={() => editor.chain().focus().redo().run()}
          disabled={!editor.can().redo()}
          title="Redo (Cmd+Shift+Z)"
        >
          <Redo className="h-3.5 w-3.5" />
        </ToolbarButton>
      </div>

      {/* Editor body */}
      <div className="px-3 py-2">
        <EditorContent editor={editor} />
      </div>
    </div>
  );
}

function ToolbarButton({
  onClick,
  active,
  disabled,
  title,
  children,
}: {
  onClick: () => void;
  active?: boolean;
  disabled?: boolean;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      title={title}
      className={cn(
        "rounded p-1 text-slate-600 transition-colors",
        "hover:bg-slate-200 hover:text-slate-900",
        active && "bg-slate-200 text-slate-900",
        disabled && "cursor-not-allowed opacity-40 hover:bg-transparent",
      )}
    >
      {children}
    </button>
  );
}
