import type { ButtonHTMLAttributes, PropsWithChildren } from "react";

type ButtonVariant = "primary" | "secondary" | "warning" | "ghost";

type ButtonProps = PropsWithChildren<
  ButtonHTMLAttributes<HTMLButtonElement> & {
    variant?: ButtonVariant;
  }
>;

const variants: Record<ButtonVariant, string> = {
  primary: "bg-slate-950 text-white hover:bg-slate-800",
  secondary: "border border-slate-200 bg-white text-slate-900 hover:border-slate-300",
  warning: "bg-amber-600 text-white hover:bg-amber-700",
  ghost: "bg-transparent text-slate-600 hover:bg-slate-100 hover:text-slate-950"
};

export function Button({ children, className = "", variant = "secondary", ...props }: ButtonProps) {
  return (
    <button
      className={[
        "inline-flex min-h-10 items-center justify-center rounded-xl px-3.5 text-sm font-semibold",
        "transition disabled:cursor-not-allowed disabled:opacity-50",
        "focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2",
        "focus-visible:outline-sky-300",
        variants[variant],
        className
      ].join(" ")}
      {...props}
    >
      {children}
    </button>
  );
}
