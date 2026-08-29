import * as React from "react"
import { cn } from "../../utils/classnames"

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "secondary" | "destructive" | "outline" | "success" | "warning" | "brand";
}

function Badge({ className, variant = "default", ...props }: BadgeProps) {
  const variants = {
    default: "border-transparent bg-slate-800 text-slate-100 hover:bg-slate-700",
    secondary: "border-transparent bg-slate-800/50 text-slate-300",
    destructive: "border-transparent bg-brand-red/20 text-brand-red hover:bg-brand-red/30",
    outline: "text-slate-300 border-slate-700",
    success: "border-transparent bg-brand-green/20 text-brand-green",
    warning: "border-transparent bg-brand-amber/20 text-brand-amber",
    brand: "border-transparent bg-brand-cyan/20 text-brand-cyan"
  };

  return (
    <div
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-slate-400 focus:ring-offset-2",
        variants[variant],
        className
      )}
      {...props}
    />
  )
}

export { Badge }
