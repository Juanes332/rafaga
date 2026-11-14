import { Toaster as Sonner, toast } from "sonner";
import { useThemeStore } from "@/stores/theme/theme.store";

type ToasterProps = React.ComponentProps<typeof Sonner>;

const Toaster = (props: ToasterProps) => {
  const theme = useThemeStore((s) => s.theme);
  return (
    <Sonner
      theme={theme}
      position="bottom-left"
      toastOptions={{
        style: {
          background: "var(--color-surface-raised)",
          color: "var(--color-ink)",
          border: "1px solid var(--color-rule)",
          borderRadius: "var(--radius-panel)",
          boxShadow: "var(--shadow-float)",
          fontFamily: "var(--font-ui)",
        },
      }}
      {...props}
    />
  );
};

export { Toaster, toast };
