// Overwrite the inlet (x=0) and outlet (x=nx-1) columns with
// equilibrium + regularized non-equilibrium from the first interior
// neighbour, both at rho = 1. A density extrapolated into the inlet
// traps acoustic waves between inlet and side walls (striations of
// +-6 % in rho); pinning it removes them. One thread per (y,z) row.
__device__ void open_column(float* __restrict__ f, long long N, long long dst,
                            long long src, float rho_set, int use_rho_set,
                            float ux, float uy, float uz, int use_u) {
    float g[Q];
    float rho = 0.f, mx = 0.f, my = 0.f, mz = 0.f;
    for (int q = 0; q < Q; ++q) {
        g[q] = f[q * N + src];
        rho += g[q]; mx += CX[q] * g[q]; my += CY[q] * g[q]; mz += CZ[q] * g[q];
    }
    float vx = mx / rho, vy = my / rho, vz = mz / rho;
    float vsq = vx * vx + vy * vy + vz * vz;
    float pxx = 0.f, pyy = 0.f, pzz = 0.f, pxy = 0.f, pxz = 0.f, pyz = 0.f;
    for (int q = 0; q < Q; ++q) {
        float cu = CX[q] * vx + CY[q] * vy + CZ[q] * vz;
        float ne = g[q] - W[q] * rho * (1.f + 3.f * cu + 4.5f * cu * cu - 1.5f * vsq);
        pxx += CX[q] * CX[q] * ne; pyy += CY[q] * CY[q] * ne; pzz += CZ[q] * CZ[q] * ne;
        pxy += CX[q] * CY[q] * ne; pxz += CX[q] * CZ[q] * ne; pyz += CY[q] * CZ[q] * ne;
    }
    float r = use_rho_set ? rho_set : rho;
    float wx = use_u ? ux : vx, wy = use_u ? uy : vy, wz = use_u ? uz : vz;
    float wsq = wx * wx + wy * wy + wz * wz;
    const float third = 1.f / 3.f;
    for (int q = 0; q < Q; ++q) {
        float cx = CX[q], cy = CY[q], cz = CZ[q];
        float cu = cx * wx + cy * wy + cz * wz;
        float qp = (cx * cx - third) * pxx + (cy * cy - third) * pyy
                 + (cz * cz - third) * pzz
                 + 2.f * (cx * cy * pxy + cx * cz * pxz + cy * cz * pyz);
        f[q * N + dst] = W[q] * r * (1.f + 3.f * cu + 4.5f * cu * cu - 1.5f * wsq)
                       + 4.5f * W[q] * qp;
    }
}

extern "C" __global__ void open_boundaries(
    float* __restrict__ f, const unsigned char* __restrict__ mask,
    const float* __restrict__ u_in, int nx, int ny, int nz) {
    long long rows = (long long)ny * nz;
    long long r = (long long)blockIdx.x * blockDim.x + threadIdx.x;
    if (r >= rows) return;
    long long N = (long long)nx * rows;
    long long base = r * nx;
    if (mask[base] != 1) {
        float uz = (DIM == 3) ? u_in[2 * rows + r] : 0.f;
        open_column(f, N, base, base + 1, 1.f, 1, u_in[r], u_in[rows + r], uz, 1);
    }
    if (mask[base + nx - 1] != 1) {
        open_column(f, N, base + nx - 1, base + nx - 2, 1.f, 1, 0.f, 0.f, 0.f, 0);
    }
}
