import type { HTMLAttributes, PropsWithChildren, ReactNode } from "react";

export function Card({
  children,
  className = "",
  ...props
}: PropsWithChildren<HTMLAttributes<HTMLElement>>) {
  return (
    <section
      className={[
        "rounded-2xl border border-slate-200 bg-white shadow-quiet-card",
        className
      ].join(" ")}
      {...props}
    >
      {children}
    </section>
  );
}

export function SectionHeader({
  action,
  eyebrow,
  title,
  description
}: {
  action?: ReactNode;
  eyebrow?: string;
  title: string;
  description?: string;
}) {
  return (
    <div className="flex items-start justify-between gap-4 border-b border-slate-200 px-5 py-4">
      <div>
        {eyebrow ? (
          <p className="mb-1 text-[11px] font-bold uppercase tracking-[0.12em] text-slate-400">
            {eyebrow}
          </p>
        ) : null}
        <h2 className="text-base font-semibold tracking-[-0.02em] text-slate-950">{title}</h2>
        {description ? <p className="mt-1 text-sm leading-6 text-slate-500">{description}</p> : null}
      </div>
      {action}
    </div>
  );
}
