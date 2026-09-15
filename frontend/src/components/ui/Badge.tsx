import * as React from "react"
import { cn } from "../../utils/classnames"

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "secondary" | "destructive" | "outline" | "success" | "warning" | "brand";
}

function Badge({ className, variant = "default", ...props }: BadgeProps) {
  const variants = {
    default: "border-transparent bg-[#F0F1EE] text-[#12201B] hover:bg-[#E7E9E4]",
    secondary: "border-transparent bg-[#F0F1EE]/60 text-[#5B6B62]",
    destructive: "border-transparent bg-brand-red/10 text-brand-red hover:bg-brand-red/20",
    outline: "text-[#5B6B62] border-[#DEE1DC]",
    success: "border-transparent bg-brand-green/10 text-brand-green",
    warning: "border-transparent bg-brand-amber/10 text-brand-amber",
    brand: "border-transparent bg-brand-cyan/10 text-brand-cyan"
  };

  return (
    <div
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-brand-cyan/40 focus:ring-offset-2",
        variants[variant],
        className
      )}
      {...props}
    />
  )
}

export { Badge }
