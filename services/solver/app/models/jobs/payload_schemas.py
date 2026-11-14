"""Job payloads of job-contract.md section 3 (fields the solver reads)."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.scene.scene_schemas import Scene


class _Loose(BaseModel):
    """Accept additive contract fields without failing."""

    model_config = ConfigDict(extra="ignore")


class Wind(_Loose):
    """Reference wind of one simulation."""

    wind_from_deg: float
    u10_ms: float = Field(gt=0)
    z0_m: float = Field(gt=0)
    analysis_height_m: float = Field(gt=0)
    ustar_ms: float | None = None
    uref_za_ms: float | None = None
    kappa: float = 0.41


class SimGrid(_Loose):
    """Rotated simulation lattice."""

    frame: Literal["wind", "section"]
    wind_from_deg: float | None = None
    origin: list[float] = Field(min_length=2, max_length=3)
    dx_m: float = Field(gt=0)
    nx: int = Field(gt=3)
    ny: int | None = None
    nz: int | None = None


class OutputGrid(_Loose):
    """Common north-up plan grid, or the (s, z) section grid."""

    frame: Literal["plan", "section"]
    dx_m: float = Field(gt=0)
    origin_x: float | None = None
    origin_y: float | None = None
    nx: int | None = None
    ny: int | None = None
    s0: float | None = None
    ns: int | None = None
    nz: int | None = None


class Grids(_Loose):
    """Simulation and output grids frozen by the api."""

    sim: SimGrid
    output: OutputGrid


class Physics(_Loose):
    """LBM parameters (ADR-12..ADR-14)."""

    u_lattice_ref: float = 0.05
    nu_lattice_floor: float = 5e-5
    smagorinsky_cs: float = 0.17
    tau_min: float = 0.5005
    tau_max: float = 2.0
    sponge_fraction: float = 0.10
    sponge_tau: float = 1.0
    inflow_perturbation: float = 0.0
    seed: int = 12345
    max_local_mach: float = 0.35
    subgrid_coverage_solid: float = 0.5
    supersampling: int = 4


class ConvergenceParams(_Loose):
    """Averaging schedule in flow-throughs (ADR-11)."""

    spinup_ft: float = Field(gt=0)
    min_avg_ft: float = Field(gt=0)
    max_avg_ft: float = Field(gt=0)
    check_every_ft: float = Field(default=0.25, gt=0)
    tolerance: float = Field(default=0.01, gt=0)
    consecutive: int = Field(default=3, gt=0)


class MemoryHint(_Loose):
    """The api's estimate, re-checked by the solver (SOL-19)."""

    estimate_bytes: int | None = None
    bytes_per_node: int | None = None
    overhead_bytes: int | None = None


class RenderHint(_Loose):
    """Preview settings."""

    dpi: int = 150
    k_accel: float = 1.2
    k_stagnation: float = 0.3


class SectionLine(_Loose):
    """Vertical cut traced from windward p0 to leeward p1."""

    p0: tuple[float, float]
    p1: tuple[float, float]


class HeavyPayload(_Loose):
    """plan2d / section2d / volume3d payload (section 3.3)."""

    contract_version: int
    job_kind: Literal["plan2d", "section2d", "volume3d"]
    project_id: str
    study_id: str
    alternative_id: str
    output_dir: str = Field(min_length=1)
    scene: Scene
    section: SectionLine | None = None
    wind: Wind
    grid: Grids
    physics: Physics = Field(default_factory=Physics)
    convergence: ConvergenceParams
    device: Literal["auto", "cpu", "gpu"] = "auto"
    memory: MemoryHint = Field(default_factory=MemoryHint)
    render: RenderHint = Field(default_factory=RenderHint)


class AggregatePayload(_Loose):
    """Lawson aggregate payload (section 3.4)."""

    contract_version: int
    job_kind: Literal["aggregate"]
    project_id: str
    study_id: str
    output_dir: str
    lawson_hash: str
    result_refs: list[dict[str, Any]]
    rose: dict[str, Any]
    site: dict[str, Any]
    lawson: dict[str, Any]
    turbulence_intensity_default: float = 0.25
    output_grid: OutputGrid


class RenderPayload(_Loose):
    """Export PNG payload (section 3.5)."""

    contract_version: int
    job_kind: Literal["render"]
    project_id: str
    export_id: str
    output_dir: str
    file_name: str = Field(pattern=r"^[A-Za-z0-9._-]+\.png$")
    layer: Literal["k", "zones", "speed", "delta_k", "lawson"]
    result_dir: str | None = None
    compare_result_dir: str | None = None
    comfort_dir: str | None = None
    output_grid: OutputGrid
    thresholds: dict[str, float] = Field(default_factory=dict)
    dpi: int = Field(default=300, ge=300)
    labels: dict[str, str] = Field(default_factory=dict)
    scene: Scene | None = None


class ReportPayload(_Loose):
    """PDF report payload (section 3.6)."""

    contract_version: int
    job_kind: Literal["report"]
    project_id: str
    report_id: str
    version: int
    output_dir: str
    file_name: str = Field(pattern=r"^[A-Za-z0-9._-]+\.pdf$")
    snapshot: dict[str, Any]
