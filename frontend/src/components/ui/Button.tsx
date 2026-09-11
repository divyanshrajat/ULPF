import * as React from "react"
import { cn } from "../../utils/classnames"

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "destructive" | "outline" | "secondary" | "ghost" | "link" | "white";
  size?: "default" | "sm" | "lg" | "icon";
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "default", size = "default", ...props }, ref) => {
    const variants = {
      default: "bg-brand-cyan text-white hover:bg-[#3A4568] font-semibold shadow-sm transition-all",
      white: "bg-brand-cyan text-white hover:bg-[#3A4568] font-semibold shadow-sm transition-all",
      destructive: "bg-brand-red text-white hover:bg-brand-red/90 font-semibold",
      outline: "border border-[#DEE1DC] bg-white hover:bg-[#F0F1EE] text-slate-900 font-medium shadow-sm transition-all",
      secondary: "bg-[#F0F1EE] text-slate-900 hover:bg-[#E7E9E4] font-medium shadow-sm",
      ghost: "text-slate-900 hover:bg-[#F0F1EE] font-medium transition-colors",
      link: "text-slate-900 underline-offset-4 hover:underline font-medium",
    };

    const sizes = {
      default: "h-10 px-4 py-2",
      sm: "h-9 rounded-md px-3 text-xs",
      lg: "h-11 rounded-md px-8 text-base",
      icon: "h-10 w-10",
    };

    return (
      <button
        ref={ref}
        className={cn(
          "inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-white transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-cyan focus-visible:ring-offset-2 disabled:pointer-events-none disabled:bg-[#EFEFEC] disabled:text-[#9CA39D] disabled:opacity-100 disabled:shadow-none",
          variants[variant],
          sizes[size],
          className
        )}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button }
