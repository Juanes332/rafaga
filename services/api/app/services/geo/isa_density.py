"""International Standard Atmosphere air density (BR-06)."""


def isa_density(elevation_m: float) -> float:
    """Return rho = 1.225 (1 - 2.25577e-5 h)^4.25588 in kg/m3."""
    return 1.225 * (1.0 - 2.25577e-5 * elevation_m) ** 4.25588
