import * as React from "react";
import * as TogglePrimitive from "@radix-ui/react-toggle";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const toggleVariants = cva(
  "inline-flex items-center justify-center gap-2 rounded-md text-[0.875rem] font-medium cursor-pointer border border-input bg-transparent text-foreground transition-colors hover:bg-[var(--color-accent-wash)] disabled:pointer-events-none disabled:opacity-50 data-[state=on]:border-primary data-[state=on]:bg-[var(--color-accent-wash)] data-[state=on]:text-primary [&_svg]:size-4",
  {
    variants: { size: { default: "h-8 px-3", sm: "h-7 px-2", lg: "h-10 px-4" } },
    defaultVariants: { size: "default" },
  },
);

const Toggle = React.forwardRef<
  React.ElementRef<typeof TogglePrimitive.Root>,
  React.ComponentPropsWithoutRef<typeof TogglePrimitive.Root> & VariantProps<typeof toggleVariants>
>(({ className, size, ...props }, ref) => <TogglePrimitive.Root ref={ref} className={cn(toggleVariants({ size, className }))} {...props} />);
Toggle.displayName = TogglePrimitive.Root.displayName;

export { Toggle, toggleVariants };
