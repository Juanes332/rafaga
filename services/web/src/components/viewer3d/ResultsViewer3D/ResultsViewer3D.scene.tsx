import { useMemo } from "react";
import { Line } from "@react-three/drei";
import * as THREE from "three";
import type { SliceData, Solid } from "./ResultsViewer3D.hook";
import { sliceRgba, type Bounds } from "./ResultsViewer3D.utils";

/** Prism for a building footprint, in ENU (the parent group maps ENU to three's y-up). */
export function SolidMesh({ solid, color }: { solid: Solid; color: string }) {
  const geometry = useMemo(() => {
    const shape = new THREE.Shape(solid.footprint.map(([x, y]) => new THREE.Vector2(x, y)));
    const g = new THREE.ExtrudeGeometry(shape, { depth: solid.z_max - solid.z_min, bevelEnabled: false });
    g.translate(0, 0, solid.z_min);
    return g;
  }, [solid]);
  return (
    <mesh geometry={geometry} castShadow>
      <meshStandardMaterial color={color} roughness={0.9} />
    </mesh>
  );
}

/** Vertical slice textured with the speed LUT. */
export function SliceMesh({ slice, max, bounds }: { slice: SliceData; max: number; bounds: Bounds }) {
  const { geometry, texture } = useMemo(() => {
    const [a0, a1, z0, z1] = slice.extents;
    const g = new THREE.PlaneGeometry(a1 - a0, z1 - z0);
    g.rotateX(Math.PI / 2);
    const mid = (a0 + a1) / 2;
    if (slice.plane === "yz") {
      g.rotateZ(Math.PI / 2);
      g.translate((bounds.min[0] + bounds.max[0]) / 2, mid, (z0 + z1) / 2);
    } else {
      g.translate(mid, (bounds.min[1] + bounds.max[1]) / 2, (z0 + z1) / 2);
    }
    const tex = new THREE.DataTexture(sliceRgba(slice.field, max), slice.field.cols, slice.field.rows, THREE.RGBAFormat);
    tex.magFilter = THREE.LinearFilter;
    tex.needsUpdate = true;
    return { geometry: g, texture: tex };
  }, [slice, max, bounds]);
  return (
    <mesh geometry={geometry}>
      <meshBasicMaterial map={texture} transparent side={THREE.DoubleSide} />
    </mesh>
  );
}

export function Streamlines({ lines, color }: { lines: number[][][]; color: string }) {
  return (
    <>
      {lines.map((l, i) => (
        <Line key={i} points={l as Array<[number, number, number]>} color={color} lineWidth={1} transparent opacity={0.75} />
      ))}
    </>
  );
}
