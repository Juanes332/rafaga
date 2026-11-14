import type { Config } from "tailwindcss";

// Tailwind only themes shadcn primitives; every value maps to a design-system token.
export default {
  content: ["./index.html", "./src/components/ui/**/*.{ts,tsx}"],
  darkMode: ["selector", '[data-theme="dark"]'],
  corePlugins: { preflight: false },
  theme: {
    extend: {
      colors: {
        background: "var(--color-ground)",
        foreground: "var(--color-ink)",
        surface: "var(--color-surface)",
        raised: "var(--color-surface-raised)",
        muted: { DEFAULT: "var(--color-surface)", foreground: "var(--color-ink-muted)" },
        primary: { DEFAULT: "var(--color-accent)", foreground: "var(--color-accent-ink)" },
        accent: { DEFAULT: "var(--color-surface)", foreground: "var(--color-ink)" },
        destructive: { DEFAULT: "var(--color-danger)", foreground: "var(--color-accent-ink)" },
        border: "var(--color-rule)",
        input: "var(--color-control-border)",
        ring: "var(--color-focus-ring)",
        popover: { DEFAULT: "var(--color-surface-raised)", foreground: "var(--color-ink)" },
      },
      borderRadius: {
        sm: "var(--radius-control)",
        md: "var(--radius-control)",
        lg: "var(--radius-panel)",
      },
      boxShadow: { float: "var(--shadow-float)", md: "var(--shadow-float)", lg: "var(--shadow-float)" },
      fontFamily: { sans: ["var(--font-ui)"], serif: ["var(--font-reading)"] },
    },
  },
  plugins: [],
} satisfies Config;
