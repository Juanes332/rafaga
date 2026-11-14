import { Link } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import { EmptyState } from "@/components/feedback/EmptyState/EmptyState";

/** Unknown route. */
export function NotFound() {
  const { t } = useTranslation();
  return (
    <main id="main" style={{ padding: "var(--space-8) var(--space-6)" }}>
      <EmptyState title={t("common:notFound")}>
        <Link to="/projects">{t("common:goProjects")}</Link>
      </EmptyState>
    </main>
  );
}
