// Velocity sets for the LBM kernels, compiled with -DDIM=2 (D2Q9) or
// -DDIM=3 (D3Q19). The order matches lattice_constants.py.
#if DIM == 2
#define Q 9
__constant__ int CX[Q] = {0, 1, 0, -1, 0, 1, -1, -1, 1};
__constant__ int CY[Q] = {0, 0, 1, 0, -1, 1, 1, -1, -1};
__constant__ int CZ[Q] = {0, 0, 0, 0, 0, 0, 0, 0, 0};
__constant__ float W[Q] = {4.f/9, 1.f/9, 1.f/9, 1.f/9, 1.f/9,
                           1.f/36, 1.f/36, 1.f/36, 1.f/36};
__constant__ int OPP[Q] = {0, 3, 4, 1, 2, 7, 8, 5, 6};
__constant__ int MY[Q] = {0, 1, 4, 3, 2, 8, 7, 6, 5};
__constant__ int MZ[Q] = {0, 1, 2, 3, 4, 5, 6, 7, 8};
#else
#define Q 19
__constant__ int CX[Q] = {0, 1, -1, 0, 0, 0, 0, 1, -1, 1, -1, 1, -1, 1, -1, 0, 0, 0, 0};
__constant__ int CY[Q] = {0, 0, 0, 1, -1, 0, 0, 1, -1, -1, 1, 0, 0, 0, 0, 1, -1, 1, -1};
__constant__ int CZ[Q] = {0, 0, 0, 0, 0, 1, -1, 0, 0, 0, 0, 1, -1, -1, 1, 1, -1, -1, 1};
__constant__ float W[Q] = {1.f/3, 1.f/18, 1.f/18, 1.f/18, 1.f/18, 1.f/18, 1.f/18,
                           1.f/36, 1.f/36, 1.f/36, 1.f/36, 1.f/36, 1.f/36,
                           1.f/36, 1.f/36, 1.f/36, 1.f/36, 1.f/36, 1.f/36};
__constant__ int OPP[Q] = {0, 2, 1, 4, 3, 6, 5, 8, 7, 10, 9, 12, 11, 14, 13, 16, 15, 18, 17};
__constant__ int MY[Q] = {0, 1, 2, 4, 3, 5, 6, 9, 10, 7, 8, 11, 12, 13, 14, 18, 17, 16, 15};
__constant__ int MZ[Q] = {0, 1, 2, 3, 4, 6, 5, 7, 8, 9, 10, 13, 14, 11, 12, 17, 18, 15, 16};
#endif

