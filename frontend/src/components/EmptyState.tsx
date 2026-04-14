export function EmptyState({ message }: { message: string }) {
  return (
    <div className="flex min-h-28 items-center justify-center rounded-xl border border-dashed border-white/10 bg-black/20 px-4 text-center text-sm text-slate-400">
      {message}
    </div>
  );
}
