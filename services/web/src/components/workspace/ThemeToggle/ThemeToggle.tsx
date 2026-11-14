import { Contrast, Moon, Sun } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { useThemeToggle } from "./ThemeToggle.hook";

const ICONS = { light: Sun, dark: Moon, system: Contrast } as const;

/** ◐ toggle in the top bar (FR-52). */
export function ThemeToggle() {
  const { theme, label, onToggle } = useThemeToggle();
  const Icon = ICONS[theme];
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Button variant="ghost" size="icon" aria-label={label} onClick={onToggle}>
          <Icon aria-hidden />
        </Button>
      </TooltipTrigger>
      <TooltipContent>{label}</TooltipContent>
    </Tooltip>
  );
}
