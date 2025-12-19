from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator
from typing import Literal

from app.routers.isa import isa_tropo  # reuse ISA speed of sound


router = APIRouter(prefix="/mach", tags=["Mach"])


SpeedUnit = Literal["m/s", "ft/s", "knots"]


class MachRequest(BaseModel):
    altitude_m: float
    speed_value: float
    speed_unit: SpeedUnit

    @field_validator("speed_value")
    @classmethod
    def speed_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Speed must be positive")
        return v


class MachResponse(BaseModel):
    altitude_m: float
    speed_input: float
    speed_unit: SpeedUnit
    speed_m_s: float
    mach: float
    speed_of_sound_m_s: float
    temperature_K: float
    flow_regime: str


@router.post("/compute", response_model=MachResponse)
def compute_mach(req: MachRequest) -> MachResponse:
    # For now, match the ISA backend limit (0–11 km)
    if req.altitude_m > 11000.0:
        raise HTTPException(
            status_code=400,
            detail="Backend Mach model currently supports up to 11,000 m (11 km).",
        )

    if req.altitude_m < 0:
        raise HTTPException(status_code=400, detail="Altitude must be non-negative")

    # ISA properties at altitude
    try:
        T, P, rho, a = isa_tropo(req.altitude_m)
    except Exception:
        raise HTTPException(status_code=500, detail="ISA model error")

    if a <= 0:
        raise HTTPException(status_code=500, detail="Invalid speed of sound")

    # Convert speed to m/s (match your frontend logic)
    if req.speed_unit == "m/s":
        V_ms = req.speed_value
    elif req.speed_unit == "ft/s":
        V_ms = req.speed_value / 3.28084
    elif req.speed_unit == "knots":
        V_ms = req.speed_value * 0.514444
    else:
        raise HTTPException(status_code=400, detail="Unsupported speed unit")

    mach = V_ms / a

    # Flow regime classification (same thresholds as your code)
    if mach < 0.3:
        regime = "Incompressible"
    elif mach < 0.8:
        regime = "Subsonic"
    elif mach < 1.2:
        regime = "Transonic"
    elif mach < 5.0:
        regime = "Supersonic"
    else:
        regime = "Hypersonic"

    return MachResponse(
        altitude_m=req.altitude_m,
        speed_input=req.speed_value,
        speed_unit=req.speed_unit,
        speed_m_s=V_ms,
        mach=mach,
        speed_of_sound_m_s=a,
        temperature_K=T,
        flow_regime=regime,
    )
