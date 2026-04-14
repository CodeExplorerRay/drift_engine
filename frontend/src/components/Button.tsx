import type { ButtonHTMLAttributes, PropsWithChildren } from "react";

type ButtonVariant = "primary" | "secondary" | "warning" | "ghost";

type ButtonProps = PropsWithChildren<
  ButtonHTMLAttributes<HTMLButtonElement> & {
    variant?: ButtonVariant;
  }
>;

const variants: Record<ButtonVariant, string> = {
  primary: "bg-sky-500 text-black hover:bg-sky-400",
  secondary: "border border-white/10 bg-white/5 text-slate-100 hover:border-white/20 hover:bg-white/10",
  warning: "bg-red-500 text-black hover:bg-red-400",
  ghost: "bg-transparent text-slate-400 hover:bg-white/5 hover:text-white"
};

export function Button({ children, className = "", variant = "secondary", ...props }: ButtonProps) {
  return (
    <button
      className={[
        "inline-flex min-h-10 items-center justify-center rounded-xl px-3.5 text-sm font-semibold",
        "transition disabled:cursor-not-allowed disabled:opacity-50",
        "focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2",
        "focus-visible:outline-sky-400",
        variants[variant],
        className
      ].join(" ")}
      {...props}
    >
      {children}
    </button>
  );
}
