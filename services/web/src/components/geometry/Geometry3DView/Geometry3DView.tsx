import { useState } from "react";
import { Canvas } from "@react-three/fiber";
import { Edges, OrbitControls } from "@react-three/drei";
import { CompassRose } from "@/components/orientation/CompassRose/CompassRose";
import { useGeometry3DData } from "@/components/geometry/Geometry3D/Geometry3D.data";
import { useThemeColors, usePrismGeometry } from "./Geometry3DView.hook";
import { AzimuthSensor } from "./Geometry3DView.azimuth";
import { frameCamera, northRotationDeg, type MeshSpec } from "./Geometry3DView.utils";
import styles from "./Geometry3DView.module.css";

function Prism({ spec, colors }: { spec: MeshSpec; colors: ReturnType<typeof useThemeColors> }) {
  const geometry = usePrismGeometry(spec);
  const color = spec.kind === "building" ? colors.building : spec.kind === "element" ? colors.element : colors.porous;
  return (
    <mesh geometry={geometry} rotation={[-Math.PI / 2, 0, 0]} position={[0, spec.zMin, 0]}>
      <meshStandardMaterial color={color} transparent={spec.opacity < 1} opacity={spec.opacity} depthWrite={spec.opacity >= 1} />
      {spec.kind !== "porous" ? <Edges color={colors.edge} /> : null}
    </mesh>
  );
}

/** react-three-fiber scene; loaded lazily so three.js stays out of the main bundle. */
export function Geometry3DView({ alternativeId, label }: { alternativeId: string | null; label: string }) {
  const specs = useGeometry3DData(alternativeId);
  const colors = useThemeColors();
  // Initial camera sits at +x/+z, i.e. azimuth 45°.
  const [azimuth, setAzimuth] = useState(Math.PI / 4);
  const cam = frameCamera(specs);
  const [tx, ty, tz] = cam.target;
  // 10 m cells over roughly twice the framed span; a 1 km grid aliases badly at the horizon.
  const grid = Math.ceil((cam.distance * 1.5) / 10) * 10;
  return (
    <div className={styles.root}>
      {/* The image role sits on the canvas only: an img's children are presentational, which would hide the compass name. */}
      <Canvas role="img" aria-label={label} camera={{ position: [tx + cam.distance * 0.7, ty + cam.distance * 0.6, tz + cam.distance * 0.7], fov: 40, near: 0.5, far: 20000 }}>
        <color attach="background" args={[colors.ground]} />
        <ambientLight intensity={0.75} />
        <directionalLight position={[200, 400, 150]} intensity={1.1} />
        <gridHelper args={[grid, grid / 10, colors.rule, colors.rule]} position={[tx, 0, tz]} />
        {specs.map((s) => (
          <Prism key={s.id} spec={s} colors={colors} />
        ))}
        <OrbitControls target={[tx, ty, tz]} makeDefault enableDamping={false} />
        <AzimuthSensor onChange={setAzimuth} />
      </Canvas>
      <CompassRose className={styles.compass} size={104} rotationDeg={northRotationDeg(azimuth)} />
    </div>
  );
}
