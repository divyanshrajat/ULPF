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
      default: "bg-white text-slate-950 hover:bg-slate-100 font-bold shadow-md shadow-white/10 transition-all",
      white: "bg-white text-slate-950 hover:bg-slate-100 font-bold shadow-md shadow-white/10 transition-all",
      destructive: "bg-brand-red text-white hover:bg-brand-red/90 font-bold",
      outline: "border-2 border-slate-200 bg-white/10 hover:bg-white hover:text-slate-950 text-white font-bold shadow-sm transition-all",
      secondary: "bg-slate-100 text-slate-900 hover:bg-white font-bold shadow-sm",
      ghost: "text-white hover:bg-white/15 hover:text-white font-medium transition-colors",
      link: "text-white underline-offset-4 hover:underline font-semibold",
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
          "inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-semibold ring-offset-slate-950 transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white focus-visible:ring-offset-2 disabled:pointer-events-none disabled:bg-slate-700 disabled:text-slate-300 disabled:opacity-60",
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
