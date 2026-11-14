// Fused pull-stream + forcing + regularized BGK/Smagorinsky collision.
// numpy_collision.py and stream_links.py are the CPU twin.
// Pull one population for node (x,y,z) applying wall rules.
__device__ __forceinline__ float pull(const float* __restrict__ fin,
                                      const unsigned char* __restrict__ mask,
                                      int q, int x, int y, int z, long long n,
                                      int nx, int ny, int nz, int ground_bb,
                                      long long N) {
    int sx = x - CX[q];
    if (sx < 0) sx += nx; else if (sx >= nx) sx -= nx;
    int sy = y - CY[q];
    int sz = z - CZ[q];
    int qq = q;
    bool bb = false;
#if DIM == 2
    if (sy < 0) { if (ground_bb) bb = true; else { sy = y; qq = MY[qq]; } }
    else if (sy >= ny) { sy = y; qq = MY[qq]; }
#else
    if (sy < 0 || sy >= ny) { sy = y; qq = MY[qq]; }
    if (sz < 0) { if (ground_bb) bb = true; else { sz = z; qq = MZ[qq]; } }
    else if (sz >= nz) { sz = z; qq = MZ[qq]; }
#endif
    if (!bb) {
        long long sn = ((long long)sz * ny + sy) * nx + sx;
        if (mask[sn] == 1) bb = true;
        else return fin[qq * N + sn];
    }
    return fin[OPP[q] * N + n];
}

// Exact implicit quadratic drag: |u| + (a/2)|u|^2 = |u*| gives
// |u|/|u*| = 2 / (1 + sqrt(1 + 2 a |u*|)); stable for any zeta.
__device__ __forceinline__ float drag_factor(float a, float speed) {
    return 2.f / (1.f + sqrtf(1.f + 2.f * a * speed));
}

extern "C" __global__ void lbm_step(
    const float* __restrict__ fin, float* __restrict__ fout,
    const unsigned char* __restrict__ mask, const unsigned short* __restrict__ pid,
    const float* __restrict__ ptable, const float* __restrict__ sponge,
    const float* __restrict__ lm2,
    float* __restrict__ avg_u, float* __restrict__ avg_u2,
    int nx, int ny, int nz, int bottom_wall, int ground_bb, float a_wall,
    float top_force, float tau0, float tau_min, float tau_max, float sponge_tau,
    float inv_count, int accumulate, const float* __restrict__ fxz, int use_fxz) {
    long long N = (long long)nx * ny * nz;
    long long n = (long long)blockIdx.x * blockDim.x + threadIdx.x;
    if (n >= N) return;
    int x = (int)(n % nx);
    long long t = n / nx;
    int y = (int)(t % ny);
    int z = (int)(t / ny);
    if (mask[n] == 1) {
        for (int q = 0; q < Q; ++q) fout[q * N + n] = W[q];
        return;
    }
    float f[Q];
    float rho = 0.f, mx = 0.f, my = 0.f, mz = 0.f;
#pragma unroll
    for (int q = 0; q < Q; ++q) {
        float v = pull(fin, mask, q, x, y, z, n, nx, ny, nz, ground_bb, N);
        f[q] = v;
        rho += v;
        mx += CX[q] * v;
        my += CY[q] * v;
        mz += CZ[q] * v;
    }
    float sx = mx / rho, sy = my / rho, sz = mz / rho;  // unforced velocity
    float ux = sx, uy = sy, uz = sz;
    int id = pid[n];
    if (id > 0) {
        const float* p = ptable + id * 5;
        float a_veg = p[4];
        if (a_veg > 0.f) {
            float s = drag_factor(a_veg, sqrtf(ux * ux + uy * uy + uz * uz));
            ux *= s; uy *= s; uz *= s;
        }
        float a_scr = p[0];
        if (a_scr > 0.f) {
            float un = ux * p[1] + uy * p[2] + uz * p[3];
            float d = un * drag_factor(a_scr, fabsf(un)) - un;
            ux += d * p[1]; uy += d * p[2]; uz += d * p[3];
        }
    }
#if DIM == 2
    if (bottom_wall && y == 0) {
        ux *= drag_factor(a_wall, fabsf(ux));
    }
    if (y == ny - 1) ux += 0.5f * top_force / rho;
#else
    if (bottom_wall && z == 0) {
        float s = drag_factor(a_wall, sqrtf(ux * ux + uy * uy));
        ux *= s; uy *= s;
    }
    if (z == nz - 1) ux += 0.5f * top_force / rho;
    if (use_fxz) ux += 0.5f * fxz[(long long)z * nx + x] / rho;
#endif
    float Fx = 2.f * rho * (ux - sx), Fy = 2.f * rho * (uy - sy), Fz = 2.f * rho * (uz - sz);
    float usq = ux * ux + uy * uy + uz * uz;
    float pxx = 0.f, pyy = 0.f, pzz = 0.f, pxy = 0.f, pxz = 0.f, pyz = 0.f;
#pragma unroll
    for (int q = 0; q < Q; ++q) {
        float cu = CX[q] * ux + CY[q] * uy + CZ[q] * uz;
        float feq = W[q] * rho * (1.f + 3.f * cu + 4.5f * cu * cu - 1.5f * usq);
        float ne = f[q] - feq;
        pxx += CX[q] * CX[q] * ne; pyy += CY[q] * CY[q] * ne; pzz += CZ[q] * CZ[q] * ne;
        pxy += CX[q] * CY[q] * ne; pxz += CX[q] * CZ[q] * ne; pyz += CY[q] * CZ[q] * ne;
    }
    float pnorm = sqrtf(pxx * pxx + pyy * pyy + pzz * pzz
                        + 2.f * (pxy * pxy + pxz * pxz + pyz * pyz));
    float tau = 0.5f * (tau0 + sqrtf(tau0 * tau0 + 25.455844f * lm2[n] * pnorm / rho));
    tau = fminf(fmaxf(tau, tau_min), tau_max);
    tau += (sponge_tau - tau) * sponge[x];
    float omn = 1.f - 1.f / tau;
    float omf = 1.f - 0.5f / tau;
    const float third = 1.f / 3.f;
#pragma unroll
    for (int q = 0; q < Q; ++q) {
        float cx = CX[q], cy = CY[q], cz = CZ[q];
        float cu = cx * ux + cy * uy + cz * uz;
        float feq = W[q] * rho * (1.f + 3.f * cu + 4.5f * cu * cu - 1.5f * usq);
        float qp = (cx * cx - third) * pxx + (cy * cy - third) * pyy
                 + (cz * cz - third) * pzz
                 + 2.f * (cx * cy * pxy + cx * cz * pxz + cy * cz * pyz);
        float cF = cx * Fx + cy * Fy + cz * Fz;
        float uF = ux * Fx + uy * Fy + uz * Fz;
        float src = W[q] * (3.f * (cF - uF) + 9.f * cu * cF);
        // Regularization drops the first moment of f - feq (= -F/2); add
        // its relaxed part back so the net momentum gain is exactly F.
        fout[q * N + n] = feq + omn * W[q] * (4.5f * qp - 1.5f * cF) + omf * src;
    }
    if (accumulate) {
        avg_u[n] += (ux - avg_u[n]) * inv_count;
        avg_u[N + n] += (uy - avg_u[N + n]) * inv_count;
#if DIM == 3
        avg_u[2 * N + n] += (uz - avg_u[2 * N + n]) * inv_count;
#endif
        avg_u2[n] += (usq - avg_u2[n]) * inv_count;
    }
}

