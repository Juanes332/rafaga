/** Fixture ids shared with other domains (studies point their jobs here). */
export const P1 = "00000000-0000-4000-8000-0000000000p1";
export const R1 = "00000000-0000-4000-8000-0000000000r1";
export const R2 = "00000000-0000-4000-8000-0000000000r2";
export const R3 = "00000000-0000-4000-8000-0000000000r3";
export const R4 = "00000000-0000-4000-8000-0000000000r4";
export const S1 = "00000000-0000-4000-8000-0000000000s1";
export const S2 = "00000000-0000-4000-8000-0000000000s2";
export const S3 = "00000000-0000-4000-8000-0000000000s3";
export const S4 = "00000000-0000-4000-8000-0000000000s4";

/** Output grid of every plan fixture: 160 × 120 cells at 1 m, lower-left (-40, -50). */
export const GRID = { frame: "plan" as const, origin_x: -40, origin_y: -50, dx_m: 1, nx: 160, ny: 120 };
export const SECTION_GRID = { frame: "section" as const, s0: -90, dx_m: 1, ns: 200, nz: 60 };
export const U_REF = 4.2;
