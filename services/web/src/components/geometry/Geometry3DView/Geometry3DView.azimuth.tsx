import { useRef } from "react";
import { useFrame, useThree } from "@react-three/fiber";
import type { OrbitControls as OrbitControlsImpl } from "three/examples/jsm/controls/OrbitControls.js";

// About 0.5°: finer changes are invisible on the compass and would re-render the overlay every frame.
const MIN_STEP_RAD = 0.0087;

/** Reports the orbit azimuth to the DOM compass overlay when it changes. */
export function AzimuthSensor({ onChange }: { onChange: (azimuthRad: number) => void }) {
  const controls = useThree((s) => s.controls) as OrbitControlsImpl | null;
  const last = useRef<number | null>(null);
  useFrame(() => {
    if (!controls) return;
    const a = controls.getAzimuthalAngle();
    if (last.current === null || Math.abs(a - last.current) > MIN_STEP_RAD) {
      last.current = a;
      onChange(a);
    }
  });
  return null;
}
