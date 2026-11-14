import { OrbitControls } from "@react-three/drei";
import { Canvas } from "@react-three/fiber";
import { useTranslation } from "react-i18next";
import { ErrorNotice } from "@/components/feedback/ErrorNotice/ErrorNotice";
import { KLegend } from "@/components/results/KLegend/KLegend";
import { useTokenColors } from "@/hooks/theme/use-token-colors";
import { useResultsViewer3D } from "./ResultsViewer3D.hook";
import { SliceMesh, SolidMesh, Streamlines } from "./ResultsViewer3D.scene";
import styles from "./ResultsViewer3D.module.css";

/** SCR-16: buildings, vertical slices and streamlines; orbit and zoom. Loaded on demand. */
export function ResultsViewer3D({ resultId }: { resultId: string }) {
  const { t } = useTranslation();
  const v = useResultsViewer3D(resultId);
  const colors = useTokenColors();
  if (v.error) return <ErrorNotice error={v.error} className={styles.notice} />;
  if (v.isLoading) return <p className={styles.loading}>{t("results:view3d.loading")}</p>;
  return (
    <div className={styles.root}>
      <div className={styles.canvas} role="img" aria-label={t("results:view3d.label")}>
        <Canvas camera={{ position: v.camera.position, fov: 40, near: 1, far: 5000 }}>
          <color attach="background" args={[colors.ground]} />
          <ambientLight intensity={0.7} />
          <directionalLight position={[200, 300, 100]} intensity={1.1} />
          <group rotation={[-Math.PI / 2, 0, 0]}>
            {v.solids.map((s) => (
              <SolidMesh key={s.id} solid={s} color="#c9d1cf" />
            ))}
            {v.slices.map((s) => (
              <SliceMesh key={s.name} slice={s} max={v.max} bounds={v.bounds} />
            ))}
            <Streamlines lines={v.streamlines} color={colors.ink} />
          </group>
          <gridHelper args={[400, 40, colors.ink, colors.ink]} position={[v.camera.target[0], 0.01, v.camera.target[2]]}>
            <lineBasicMaterial attach="material" transparent opacity={0.08} />
          </gridHelper>
          <OrbitControls target={v.camera.target} makeDefault />
        </Canvas>
      </div>
      <div className={styles.legend}>
        <KLegend kind="speed" max={v.max} />
        <p className={styles.help}>{t("results:view3d.help")}</p>
      </div>
    </div>
  );
}

export default ResultsViewer3D;
