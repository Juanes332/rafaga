import { Link } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { useAccountMenu } from "./AccountMenu.hook";
import styles from "./AccountMenu.module.css";

/** Account menu: settings, users (architects), templates, sign out. */
export function AccountMenu() {
  const { t } = useTranslation();
  const m = useAccountMenu();
  return (
    <DropdownMenu>
      <DropdownMenuTrigger className={styles.trigger}>
        <span className="sr-only">{t("common:nav.account")}</span>
        <span className={styles.email}>{m.email}</span>
        <span className={styles.initial} aria-hidden>
          {m.initial}
        </span>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem asChild>
          <Link to="/settings">{t("common:nav.settings")}</Link>
        </DropdownMenuItem>
        <DropdownMenuItem asChild>
          <Link to="/templates">{t("common:nav.templates")}</Link>
        </DropdownMenuItem>
        {m.isArchitect ? (
          <DropdownMenuItem asChild>
            <Link to="/users">{t("common:nav.users")}</Link>
          </DropdownMenuItem>
        ) : null}
        <DropdownMenuSeparator />
        <DropdownMenuItem onSelect={m.onLogout}>{t("common:nav.logout")}</DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
