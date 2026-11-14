import { useTranslation } from "react-i18next";
import type { EdgeRef } from "@/stores/facades/facades.store";
import type { FacadeElement } from "@/types/facades/facade.types";
import styles from "./ElementsList.module.css";

interface ElementsListProps {
  elements: FacadeElement[];
  buildingName: (id: string) => string;
  onSelect: (edge: EdgeRef) => void;
}

/** Strategies of the open alternative; choosing one selects its edge for editing. */
export function ElementsList({ elements, buildingName, onSelect }: ElementsListProps) {
  const { t } = useTranslation();
  return (
    <section className={styles.root} aria-labelledby="elements-title">
      <h2 id="elements-title" className={styles.title}>
        {t("alternatives:elements.title")}
      </h2>
      {elements.length === 0 ? <p className={styles.empty}>{t("alternatives:elements.empty")}</p> : null}
      <ul className={styles.list}>
        {elements.map((el) => (
          <li key={el.id}>
            <button type="button" className={styles.item} onClick={() => onSelect({ buildingId: el.building_id, edgeIndex: el.edge_index })}>
              {t("alternatives:elements.item", {
                strategy: t(`alternatives:strategies.${el.type}`),
                index: el.edge_index + 1,
                building: buildingName(el.building_id),
              })}
            </button>
            {el.orphaned ? <p className={styles.orphan}>{t("alternatives:elements.orphaned")}</p> : null}
          </li>
        ))}
      </ul>
    </section>
  );
}
