from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator
import math


router = APIRouter(prefix="/mission-planner", tags=["Mission Planner"])


class MissionPlanRequest(BaseModel):
    Wi_kg: float            # total initial mass [kg]
    fuel_weight_kg: float   # fuel mass [kg]
    cruise_speed_ms: float  # cruise speed [m/s]
    c_per_hr: float         # SFC [1/hr]
    LD: float               # lift-to-drag ratio

    @field_validator("Wi_kg", "fuel_weight_kg", "cruise_speed_ms", "c_per_hr", "LD")
    @classmethod
    def positive_values(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Values must be positive")
        return v


class MissionPlanResponse(BaseModel):
    Wi_kg: float
    Wf_kg: float
    fuel_weight_kg: float

    range_m: float
    range_km: float
    range_nm: float
    range_mi: float

    time_hr: float


@router.post("/estimate", response_model=MissionPlanResponse)
def estimate_mission(req: MissionPlanRequest) -> MissionPlanResponse:
    Wi = req.Wi_kg
    W_fuel = req.fuel_weight_kg
    V = req.cruise_speed_ms
    c = req.c_per_hr
    LD = req.LD

    Wf = Wi - W_fuel

    if Wf <= 0 or Wi <= Wf:
        raise HTTPException(
            status_code=400,
            detail="Invalid weight combination. Make sure fuel weight is positive and initial weight is greater than initial weight.",
        )

    c_sec = c / 3600.0  # [1/s]

    # Breguet range (mass form)
    try:
        R_m = (V / c_sec) * LD * math.log(Wi / Wf)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid input combination for Breguet equation. Check Wi/Wf and parameters.",
        )

    R_km = R_m / 1000.0
    R_nm = R_km * 0.539957
    R_mi = R_km * 0.621371

    # Flight time
    time_hr = R_m / V / 3600.0

    return MissionPlanResponse(
        Wi_kg=Wi,
        Wf_kg=Wf,
        fuel_weight_kg=W_fuel,
        range_m=R_m,
        range_km=R_km,
        range_nm=R_nm,
        range_mi=R_mi,
        time_hr=time_hr,
    )
