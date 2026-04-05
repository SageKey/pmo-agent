import { TopBar } from "@/components/layout/TopBar";

export function Placeholder({ title }: { title: string }) {
  return (
    <>
      <TopBar title={title} subtitle="Coming in a later slice." />
      <div className="p-8">
        <div className="rounded-xl border border-dashed border-slate-200 bg-white p-16 text-center text-sm text-slate-500">
          This page will be ported from the Streamlit equivalent in a future slice.
        </div>
      </div>
    </>
  );
}
