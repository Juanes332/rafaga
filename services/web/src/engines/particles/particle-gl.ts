import { DRAW_FS, DRAW_VS, FILL_FS, QUAD_VS, UPDATE_FS } from "./particle-gl.shaders";
import { compile, floatTexture, padRg, seedState, uniforms } from "./particle-gl.utils";
import { MAX_PX, PX_PER_K, upwindEdge, type VelocityData } from "./particles.math";

const STATE_W = 128;
const SPAWN_W = 2048;
type U = Record<string, WebGLUniformLocation | null>;

export interface ParticleView {
  view: [number, number, number, number];
  ppc: number;
  zoom: number;
}

/** WebGL2 ping-pong particle advection with fading trails (WEB-03). */
export class ParticleRenderer {
  private state: WebGLTexture[] = [];
  private fbo: WebGLFramebuffer[] = [];
  private cur = 0;
  private count = 0;
  private view: ParticleView = { view: [0, 0, 0, 0], ppc: 1, zoom: 1 };
  private readonly upd: { p: WebGLProgram; u: U };
  private readonly draw: { p: WebGLProgram; u: U };
  private readonly fill: { p: WebGLProgram; u: U };
  private readonly vel: WebGLTexture;
  private readonly spawn: WebGLTexture;
  private readonly upwind: [number, number, number, number];

  /** Null when WebGL2 or float render targets are missing → caller shows static streamlines. */
  static create(canvas: HTMLCanvasElement, data: VelocityData, cols: number, rows: number, count: number): ParticleRenderer | null {
    const gl = canvas.getContext("webgl2", { premultipliedAlpha: true, preserveDrawingBuffer: true, antialias: false, alpha: true });
    if (!gl || !gl.getExtension("EXT_color_buffer_float")) return null;
    try {
      return new ParticleRenderer(gl, data, cols, rows, count);
    } catch {
      return null;
    }
  }

  private constructor(
    private readonly gl: WebGL2RenderingContext,
    private readonly data: VelocityData,
    private readonly cols: number,
    private readonly rows: number,
    count: number,
  ) {
    const quad = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, quad);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
    gl.enableVertexAttribArray(0);
    gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0);
    const updNames = ["u_state", "u_vel", "u_spawn", "u_grid", "u_cellsPerK", "u_maxCells", "u_seed", "u_spawnCount", "u_spawnW", "u_upwind"];
    this.upd = { p: compile(gl, QUAD_VS, UPDATE_FS), u: {} };
    this.upd.u = uniforms(gl, this.upd.p, updNames);
    this.draw = { p: compile(gl, DRAW_VS, DRAW_FS), u: {} };
    this.draw.u = uniforms(gl, this.draw.p, ["u_state", "u_stateW", "u_view", "u_size", "u_color"]);
    this.fill = { p: compile(gl, QUAD_VS, FILL_FS), u: {} };
    this.fill.u = uniforms(gl, this.fill.p, ["u_color"]);
    this.vel = floatTexture(gl, cols, rows, 2, data.velocity);
    const sp = padRg(data.fluid, data.fluidCount, SPAWN_W);
    this.spawn = floatTexture(gl, SPAWN_W, sp.h, 2, sp.data);
    this.upwind = upwindEdge(data.meanU, data.meanV, cols, rows);
    this.setCount(count);
  }

  get particles(): number {
    return this.count;
  }

  setCount(count: number): void {
    const gl = this.gl;
    this.state.forEach((t) => gl.deleteTexture(t));
    this.fbo.forEach((f) => gl.deleteFramebuffer(f));
    this.count = Math.ceil(count / STATE_W) * STATE_W;
    const h = this.count / STATE_W;
    const init = seedState(this.data.fluid, this.data.fluidCount, this.count);
    this.state = [floatTexture(gl, STATE_W, h, 4, init), floatTexture(gl, STATE_W, h, 4, null)];
    this.fbo = this.state.map((t) => {
      const f = gl.createFramebuffer() as WebGLFramebuffer;
      gl.bindFramebuffer(gl.FRAMEBUFFER, f);
      gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, t, 0);
      return f;
    });
    gl.bindFramebuffer(gl.FRAMEBUFFER, null);
  }

  setView(view: ParticleView): void {
    this.view = view;
    this.clearTrails();
  }

  /** Zoom/pan restart trails without a flash: just clear the trail buffer. */
  clearTrails(): void {
    const gl = this.gl;
    gl.bindFramebuffer(gl.FRAMEBUFFER, null);
    gl.clearColor(0, 0, 0, 0);
    gl.clear(gl.COLOR_BUFFER_BIT);
  }

  private bindTex(unit: number, tex: WebGLTexture, loc: WebGLUniformLocation | null): void {
    this.gl.activeTexture(this.gl.TEXTURE0 + unit);
    this.gl.bindTexture(this.gl.TEXTURE_2D, tex);
    this.gl.uniform1i(loc, unit);
  }

  private step(): void {
    const { gl, upd } = this;
    const next = 1 - this.cur;
    gl.bindFramebuffer(gl.FRAMEBUFFER, this.fbo[next]);
    gl.viewport(0, 0, STATE_W, this.count / STATE_W);
    gl.disable(gl.BLEND);
    gl.useProgram(upd.p);
    this.bindTex(0, this.state[this.cur], upd.u.u_state);
    this.bindTex(1, this.vel, upd.u.u_vel);
    this.bindTex(2, this.spawn, upd.u.u_spawn);
    gl.uniform2f(upd.u.u_grid, this.cols, this.rows);
    gl.uniform1f(upd.u.u_cellsPerK, (PX_PER_K * this.view.zoom) / this.view.ppc);
    gl.uniform1f(upd.u.u_maxCells, MAX_PX / this.view.ppc);
    gl.uniform1f(upd.u.u_seed, Math.random() * 100);
    gl.uniform1i(upd.u.u_spawnCount, this.data.fluidCount);
    gl.uniform1i(upd.u.u_spawnW, SPAWN_W);
    gl.uniform4f(upd.u.u_upwind, ...this.upwind);
    gl.drawArrays(gl.TRIANGLES, 0, 3);
    this.cur = next;
  }

  private fillQuad(r: number, g: number, b: number, a: number): void {
    this.gl.useProgram(this.fill.p);
    this.gl.uniform4f(this.fill.u.u_color, r, g, b, a);
    this.gl.drawArrays(this.gl.TRIANGLES, 0, 3);
  }

  /** One frame: advect, fade trails 4 %, draw particles in ink (premultiplied rgba 0..1). */
  frame(color: [number, number, number, number]): void {
    const gl = this.gl;
    this.step();
    gl.bindFramebuffer(gl.FRAMEBUFFER, null);
    gl.viewport(0, 0, gl.drawingBufferWidth, gl.drawingBufferHeight);
    gl.enable(gl.BLEND);
    gl.blendEquation(gl.FUNC_ADD);
    gl.blendFunc(gl.ZERO, gl.SRC_ALPHA);
    this.fillQuad(0, 0, 0, 0.96);
    // 8-bit buffers never reach zero by multiplying alone; a tiny subtract clears ghosts.
    gl.blendEquation(gl.FUNC_REVERSE_SUBTRACT);
    gl.blendFunc(gl.ONE, gl.ONE);
    this.fillQuad(1.5 / 255, 1.5 / 255, 1.5 / 255, 1.5 / 255);
    gl.blendEquation(gl.FUNC_ADD);
    gl.blendFunc(gl.ONE, gl.ONE_MINUS_SRC_ALPHA);
    gl.useProgram(this.draw.p);
    this.bindTex(0, this.state[this.cur], this.draw.u.u_state);
    gl.uniform1i(this.draw.u.u_stateW, STATE_W);
    gl.uniform4f(this.draw.u.u_view, ...this.view.view);
    gl.uniform1f(this.draw.u.u_size, Math.max(1, window.devicePixelRatio));
    gl.uniform4f(this.draw.u.u_color, color[0] * color[3], color[1] * color[3], color[2] * color[3], color[3]);
    gl.drawArrays(gl.POINTS, 0, this.count);
  }

  dispose(): void {
    const gl = this.gl;
    this.state.forEach((t) => gl.deleteTexture(t));
    this.fbo.forEach((f) => gl.deleteFramebuffer(f));
    gl.deleteTexture(this.vel);
    gl.deleteTexture(this.spawn);
  }
}
