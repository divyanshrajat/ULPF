import * as React from "react"
import { cn } from "../../utils/classnames"

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "destructive" | "outline" | "secondary" | "ghost" | "link";
  size?: "default" | "sm" | "lg" | "icon";
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "default", size = "default", ...props }, ref) => {
    const variants = {
      default: "bg-brand-cyan text-slate-950 hover:bg-brand-cyan/90",
      destructive: "bg-brand-red text-slate-50 hover:bg-brand-red/90",
      outline: "border border-slate-700 bg-transparent hover:bg-slate-800 text-slate-100",
      secondary: "bg-slate-800 text-slate-100 hover:bg-slate-800/80",
      ghost: "hover:bg-slate-800 hover:text-slate-100 text-slate-300",
      link: "text-brand-cyan underline-offset-4 hover:underline",
    };

    const sizes = {
      default: "h-10 px-4 py-2",
      sm: "h-9 rounded-md px-3",
      lg: "h-11 rounded-md px-8",
      icon: "h-10 w-10",
    };

    return (
      <button
        ref={ref}
        className={cn(
          "inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-slate-950 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-400 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
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
