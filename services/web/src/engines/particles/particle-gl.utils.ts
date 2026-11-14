/** Small WebGL2 helpers kept apart from the renderer's frame logic. */

export function compile(gl: WebGL2RenderingContext, vs: string, fs: string): WebGLProgram {
  const program = gl.createProgram() as WebGLProgram;
  for (const [type, src] of [[gl.VERTEX_SHADER, vs], [gl.FRAGMENT_SHADER, fs]] as const) {
    const shader = gl.createShader(type) as WebGLShader;
    gl.shaderSource(shader, src);
    gl.compileShader(shader);
    if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(shader) ?? "shader");
    gl.attachShader(program, shader);
  }
  gl.bindAttribLocation(program, 0, "a_pos");
  gl.linkProgram(program);
  if (!gl.getProgramParameter(program, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(program) ?? "link");
  return program;
}

/** Float texture with NEAREST sampling (the shader interpolates by hand with texelFetch). */
export function floatTexture(gl: WebGL2RenderingContext, w: number, h: number, channels: 2 | 4, data: Float32Array | null): WebGLTexture {
  const tex = gl.createTexture() as WebGLTexture;
  gl.bindTexture(gl.TEXTURE_2D, tex);
  const [internal, format] = channels === 2 ? [gl.RG32F, gl.RG] : [gl.RGBA32F, gl.RGBA];
  gl.texImage2D(gl.TEXTURE_2D, 0, internal, w, h, 0, format, gl.FLOAT, data);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
  return tex;
}

/** Pad a flat RG array to a w × h texture (rows of `w`). */
export function padRg(data: Float32Array, count: number, w: number): { data: Float32Array; h: number } {
  const h = Math.max(1, Math.ceil(count / w));
  const out = new Float32Array(w * h * 2);
  out.set(data.subarray(0, count * 2));
  return { data: out, h };
}

/** Initial particle state: random fluid cells with staggered ages. */
export function seedState(fluid: Float32Array, fluidCount: number, count: number): Float32Array {
  const s = new Float32Array(count * 4);
  for (let i = 0; i < count; i += 1) {
    const j = Math.floor(Math.random() * Math.max(fluidCount, 1));
    s[i * 4] = fluid[j * 2] + Math.random() - 0.5;
    s[i * 4 + 1] = fluid[j * 2 + 1] + Math.random() - 0.5;
    s[i * 4 + 3] = 120 + Math.random() * 240;
    s[i * 4 + 2] = Math.random() * s[i * 4 + 3];
  }
  return s;
}

export function uniforms(gl: WebGL2RenderingContext, p: WebGLProgram, names: string[]): Record<string, WebGLUniformLocation | null> {
  return Object.fromEntries(names.map((n) => [n, gl.getUniformLocation(p, n)]));
}
