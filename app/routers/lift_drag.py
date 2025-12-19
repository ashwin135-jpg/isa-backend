from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator
from typing import Literal, Optional

from app.routers.isa import isa_tropo  # reuse ISA for density, temperature


router = APIRouter(prefix="/lift-drag", tags=["Lift & Drag"])


AltUnit = Literal["meters", "feet", "kilometers"]
SpeedUnit = Literal["m/s", "kt", "ft/s"]
AreaUnit = Literal["m2", "ft2"]
WeightUnit = Literal["N", "lbf"]


class LiftDragRequest(BaseModel):
    altitude_value: float
    altitude_unit: AltUnit
    speed_value: float
    speed_unit: SpeedUnit
    wing_area_value: float
    wing_area_unit: AreaUnit
    cl: float
    cd: float
    weight_value: Optional[float] = None
    weight_unit: Optional[WeightUnit] = None

    @field_validator("speed_value", "wing_area_value")
    @classmethod
    def must_be_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Value must be positive")
        return v


class LiftDragResponse(BaseModel):
    altitude_m: float
    rho_kg_m3: float
    temperature_K: float
    speed_m_s: float
    q_Pa: float
    lift_N: float
    drag_N: float
    ld_ratio: float
    wing_area_m2: float
    cl: float
    cd: float
    weight_N: Optional[float] = None
    load_factor: Optional[float] = None
    lift_excess_N: Optional[float] = None


def _to_meters(altitude_value: float, unit: AltUnit) -> float:
    if unit == "meters":
        return altitude_value
    elif unit == "feet":
        return altitude_value * 0.3048
    else:  # kilometers
        return altitude_value * 1000.0


def _to_m_s(speed: float, unit: SpeedUnit) -> float:
    if unit == "m/s":
        return speed
    elif unit == "ft/s":
        return speed * 0.3048
    else:  # kt
        return speed * 0.514444


def _to_m2(area: float, unit: AreaUnit) -> float:
    if unit == "m2":
        return area
    else:  # ft^2
        return area * 0.092903  # ft^2 -> m^2


def _to_newtons(weight: float, unit: WeightUnit) -> float:
    if unit == "N":
        return weight
    else:  # lbf
        return weight * 4.4482216153


@router.post("/compute", response_model=LiftDragResponse)
def compute_lift_drag(req: LiftDragRequest) -> LiftDragResponse:
    # Convert altitude to meters
    alt_m = _to_meters(req.altitude_value, req.altitude_unit)

    if alt_m < 0:
        raise HTTPException(status_code=400, detail="Altitude must be non-negative")

    # For now, clamp to ISA troposphere like other endpoints
    alt_m_clamped = max(0.0, min(11000.0, alt_m))

    # ISA atmosphere
    T, P, rho, a = isa_tropo(alt_m_clamped)
    if rho <= 0:
        raise HTTPException(status_code=500, detail="Invalid air density from ISA")

    # Convert speed and area
    V_ms = _to_m_s(req.speed_value, req.speed_unit)
    S_m2 = _to_m2(req.wing_area_value, req.wing_area_unit)

    # Dynamic pressure
    q = 0.5 * rho * V_ms ** 2  # [Pa = N/m^2]

    # Lift & drag
    L = q * S_m2 * req.cl
    D = q * S_m2 * req.cd

    ld_ratio = L / D if D > 0 else 0.0

    # Optional: weight-based metrics
    W_N = None
    load_factor = None
    L_excess = None

    if req.weight_value is not None and req.weight_unit is not None:
        W_N = _to_newtons(req.weight_value, req.weight_unit)
        if W_N > 0:
            load_factor = L / W_N
            L_excess = L - W_N

    return LiftDragResponse(
        altitude_m=alt_m_clamped,
        rho_kg_m3=rho,
        temperature_K=T,
        speed_m_s=V_ms,
        q_Pa=q,
        lift_N=L,
        drag_N=D,
        ld_ratio=ld_ratio,
        wing_area_m2=S_m2,
        cl=req.cl,
        cd=req.cd,
        weight_N=W_N,
        load_factor=load_factor,
        lift_excess_N=L_excess,
    )
