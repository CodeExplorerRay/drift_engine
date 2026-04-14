import type { HTMLAttributes, PropsWithChildren, ReactNode } from "react";

export function Card({
  children,
  className = "",
  ...props
}: PropsWithChildren<HTMLAttributes<HTMLElement>>) {
  return (
    <section
      className={[
        "rounded-2xl border border-white/5 bg-[#11161d] shadow-[0_24px_80px_rgba(0,0,0,0.24)]",
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
    <div className="flex items-start justify-between gap-4 border-b border-white/5 px-5 py-4">
      <div>
        {eyebrow ? (
          <p className="mb-1 text-[11px] font-bold uppercase tracking-[0.12em] text-slate-500">
            {eyebrow}
          </p>
        ) : null}
        <h2 className="text-base font-semibold tracking-[-0.02em] text-white">{title}</h2>
        {description ? <p className="mt-1 text-sm leading-6 text-slate-400">{description}</p> : null}
      </div>
      {action}
    </div>
  );
}
