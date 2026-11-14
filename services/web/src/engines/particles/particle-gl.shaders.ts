/** GLSL 300 es sources for the particle field (design-system §7). */

export const QUAD_VS = `#version 300 es
in vec2 a_pos;
void main() { gl_Position = vec4(a_pos, 0.0, 1.0); }`;

// Advection: state texel = (x, y, age, life) in cell units / frames.
export const UPDATE_FS = `#version 300 es
precision highp float;
precision highp int;
uniform sampler2D u_state;
uniform sampler2D u_vel;
uniform sampler2D u_spawn;
uniform vec2 u_grid;
uniform float u_cellsPerK;
uniform float u_maxCells;
uniform float u_seed;
uniform int u_spawnCount;
uniform int u_spawnW;
uniform vec4 u_upwind;
out vec4 o;

float hash(vec2 p) { return fract(sin(dot(p, vec2(12.9898, 78.233)) + u_seed) * 43758.5453); }

vec2 velAt(vec2 p) {
  vec2 g = clamp(p - 0.5, vec2(0.0), u_grid - 1.0);
  ivec2 c0 = ivec2(floor(g));
  ivec2 c1 = min(c0 + 1, ivec2(u_grid) - 1);
  vec2 t = g - vec2(c0);
  vec2 a = texelFetch(u_vel, c0, 0).xy;
  vec2 b = texelFetch(u_vel, ivec2(c1.x, c0.y), 0).xy;
  vec2 c = texelFetch(u_vel, ivec2(c0.x, c1.y), 0).xy;
  vec2 d = texelFetch(u_vel, c1, 0).xy;
  return mix(mix(a, b, t.x), mix(c, d, t.x), t.y);
}

vec2 fluidCell(float r) {
  int i = int(r * float(u_spawnCount)) % max(u_spawnCount, 1);
  return texelFetch(u_spawn, ivec2(i % u_spawnW, i / u_spawnW), 0).xy;
}

void main() {
  vec2 id = gl_FragCoord.xy;
  vec4 s = texelFetch(u_state, ivec2(id), 0);
  vec2 p = s.xy;
  float age = s.z + 1.0;
  float life = s.w;
  vec2 v = velAt(p);
  vec2 d = v * u_cellsPerK;
  float m = length(d);
  if (m > u_maxCells) d *= u_maxCells / m;
  p += d;
  float r = hash(id + p);
  bool outside = p.x < 0.0 || p.y < 0.0 || p.x >= u_grid.x || p.y >= u_grid.y;
  if (age > life || outside || length(v) < 1e-4 || r < 0.003) {
    float r2 = hash(id * 1.37 + 7.0);
    // 0.3 % of particles re-enter upwind to keep the supply; the rest respawn in fluid cells.
    // A light upwind trickle (deep band) offsets the downstream drift; everything else respawns uniformly.
    vec2 inward = normalize(vec2(u_upwind.y - u_upwind.w, u_upwind.z - u_upwind.x)) * sign(dot(u_grid * 0.5 - u_upwind.xy, normalize(vec2(u_upwind.y - u_upwind.w, u_upwind.z - u_upwind.x))));
    vec2 entry = mix(u_upwind.xy, u_upwind.zw, r2) + inward * hash(id + 9.3) * 0.25 * max(u_grid.x, u_grid.y);
    p = r < 0.0001 ? entry : fluidCell(r2) + (vec2(hash(id + 3.1), hash(id + 5.7)) - 0.5);
    age = 0.0;
    life = 120.0 + hash(id * 2.11) * 240.0;
  }
  o = vec4(p, age, life);
}`;

export const DRAW_VS = `#version 300 es
precision highp float;
uniform sampler2D u_state;
uniform int u_stateW;
uniform vec4 u_view;
uniform float u_size;
out float v_alpha;
void main() {
  vec4 s = texelFetch(u_state, ivec2(gl_VertexID % u_stateW, gl_VertexID / u_stateW), 0);
  gl_Position = vec4(s.x * u_view.x + u_view.z, s.y * u_view.y + u_view.w, 0.0, 1.0);
  gl_PointSize = u_size;
  // Fade in at birth and out at death so respawns never pop.
  v_alpha = smoothstep(0.0, 12.0, s.z) * (1.0 - smoothstep(s.w - 12.0, s.w, s.z));
}`;

export const DRAW_FS = `#version 300 es
precision mediump float;
uniform vec4 u_color;
in float v_alpha;
out vec4 o;
void main() { o = u_color * v_alpha; }`;

export const FILL_FS = `#version 300 es
precision mediump float;
uniform vec4 u_color;
out vec4 o;
void main() { o = u_color; }`;
