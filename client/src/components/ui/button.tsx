"use client"

import { Button as ButtonPrimitive } from "@base-ui/react/button"
import { cva, type VariantProps } from "class-variance-authority"
import { Slot } from "@radix-ui/react-slot"

import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "group/button inline-flex shrink-0 items-center justify-center rounded-md border-2 border-border text-sm font-bold whitespace-nowrap transition-all outline-none select-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground shadow-brutalist hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-[2px_2px_var(--border)] active:translate-x-[4px] active:translate-y-[4px] active:shadow-none",
        outline: "bg-background text-foreground shadow-brutalist hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-[2px_2px_var(--border)] active:translate-x-[4px] active:translate-y-[4px] active:shadow-none",
        secondary: "bg-secondary text-secondary-foreground shadow-brutalist hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-[2px_2px_var(--border)] active:translate-x-[4px] active:translate-y-[4px] active:shadow-none",
        ghost: "border-transparent bg-transparent hover:bg-muted hover:text-foreground",
        destructive: "bg-destructive text-destructive-foreground shadow-brutalist hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-[2px_2px_var(--border)] active:translate-x-[4px] active:translate-y-[4px] active:shadow-none",
        link: "border-transparent bg-transparent text-primary underline-offset-4 hover:underline",
      },
      size: {
        default:
          "h-9 gap-1.5 px-4",
        xs: "h-6 gap-1 rounded-sm px-2 text-xs [&_svg:not([class*='size-'])]:size-3",
        sm: "h-8 gap-1.5 rounded-sm px-3 text-xs [&_svg:not([class*='size-'])]:size-3.5",
        lg: "h-10 gap-2 px-5 text-base",
        icon: "size-9",
        "icon-xs":
          "size-6 rounded-sm [&_svg:not([class*='size-'])]:size-3",
        "icon-sm":
          "size-8 rounded-sm",
        "icon-lg": "size-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

function Button({
  asChild = false,
  className,
  variant = "default",
  size = "default",
  ...props
}: ButtonPrimitive.Props & VariantProps<typeof buttonVariants> & { asChild?: boolean }) {
  const classNames = cn(buttonVariants({ variant, size, className }))

  if (asChild) {
    // @ts-ignore - Slot and ButtonPrimitive have incompatible prop types
    return <Slot data-slot="button" className={classNames} {...props} />
  }

  return (
    <ButtonPrimitive
      data-slot="button"
      className={classNames}
      {...props}
    />
  )
}

export { Button, buttonVariants }
