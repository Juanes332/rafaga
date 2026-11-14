import type { StrategyInput } from "@/lib/compare/strategy-summary";

/** Same numbers and sentences are asserted by services/solver/tests/services/report/test_report_summary.py. */
export const GOLDEN: { input: StrategyInput; sentences: string[] } = {
  input: {
    name: "Celosía 40 %",
    baseName: "Caso base",
    ka: [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
    kb: [0.6, 0.6, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
    dkReduction: -0.1,
    areas: { reductionM2: 200, accelA: 800, accelB: 500 },
    comfort: {
      classesA: { A: 100, B: 200, C: 1000, D: 50, E: 0 },
      classesB: { A: 100, B: 520, C: 680, D: 50, E: 0 },
      unsafeA: 40,
      unsafeB: 10,
    },
  },
  sentences: [
    "Celosía 40 % reduce el viento un 40 % en la zona protegida (200 m²).",
    "Las zonas de aceleración pasan de 800 m² a 500 m².",
    "Unos 320 m² pasan de la clase C (Pasear) a la clase B (Estar de pie).",
    "Al menos 320 m² mejoran de clase.",
    "El área con ráfagas fuertes pasa de 40 m² a 10 m².",
    "Veredicto: mejora frente a Caso base.",
  ],
};
