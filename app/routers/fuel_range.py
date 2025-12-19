from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator
import math


router = APIRouter(prefix="/fuel-range", tags=["Fuel & Range"])


class FuelRangeRequest(BaseModel):
    V_ms: float                # cruise speed [m/s]
    pax: int                   # passenger count
    pax_wt_kg: float           # avg passenger weight [kg]
    W_empty_kg: float          # empty mass [kg]
    W_fuel_kg: float           # fuel mass [kg]
    c_per_hr: float            # SFC [1/hr]
    LD: float                  # lift-to-drag ratio
    S_m2: float                # wing area [m^2]
    b_m: float                 # wingspan [m]
    CD0: float                 # zero-lift drag coefficient
    e: float                   # Oswald efficiency

    @field_validator("V_ms", "pax_wt_kg", "W_empty_kg", "W_fuel_kg", "c_per_hr", "LD", "S_m2", "b_m")
    @classmethod
    def positive_values(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Values must be positive")
        return v


class FuelRangeResponse(BaseModel):
    Wi_kg: float
    Wf_kg: float
    W_pax_kg: float

    range_m: float
    range_km: float
    range_nm: float

    endurance_hr: float

    fuel_burn_time_sec: float
    fuel_burn_time_min: float
    fuel_burn_time_hr: float

    rho_kg_m3: float
    q_Pa: float
    CL: float
    AR: float
    k: float
    CD: float
    drag_N: float

    fuel_burn_rate_kg_s: float
    V_ms: float


@router.post("/estimate", response_model=FuelRangeResponse)
def estimate_fuel_and_range(req: FuelRangeRequest) -> FuelRangeResponse:
    V = req.V_ms
    pax = req.pax
    pax_wt = req.pax_wt_kg
    W_empty = req.W_empty_kg
    W_fuel = req.W_fuel_kg
    c = req.c_per_hr
    LD = req.LD
    S = req.S_m2
    b = req.b_m
    CD0 = req.CD0
    e = req.e

    # Derived weights
    W_pax = pax * pax_wt               # kg
    Wi = W_empty + W_fuel + W_pax      # initial mass [kg]
    Wf = Wi - W_fuel                   # final mass [kg]

    if Wf <= 0 or Wi <= Wf:
        raise HTTPException(
            status_code=400,
            detail="Invalid weight combination. Make sure fuel weight is positive and initial weight is greater than final weight.",
        )

    g = 9.81
    c_sec = c / 3600.0                 # [1/s]

    # --- Breguet Jet Range ---
    range_m = (V / c_sec) * LD * math.log(Wi / Wf)
    range_km = range_m / 1000.0
    range_nm = range_km * 0.539957

    # Endurance
    endurance_hr = (1.0 / c) * LD * math.log(Wi / Wf)

    # --- Simple drag-based thrust/fuel model (sea level rho) ---
    rho = 1.225
    q = 0.5 * rho * V**2
    L = Wi * g
    CL = L / (q * S)
    AR = b**2 / S
    k = 1.0 / (math.pi * e * AR)
    CD = CD0 + k * CL**2
    D = q * S * CD                      # drag [N] ≈ thrust required [N]

    fuel_burn_rate = c_sec * D          # kg/s (approx)
    if fuel_burn_rate <= 0:
        raise HTTPException(
            status_code=400,
            detail="Computed fuel burn rate is non-positive. Check inputs."
        )

    # time to burn all fuel
    t_sec = W_fuel / fuel_burn_rate     # kg / (kg/s) = s
    t_min = t_sec / 60.0
    t_hr = t_sec / 3600.0

    return FuelRangeResponse(
        Wi_kg=Wi,
        Wf_kg=Wf,
        W_pax_kg=W_pax,
        range_m=range_m,
        range_km=range_km,
        range_nm=range_nm,
        endurance_hr=endurance_hr,
        fuel_burn_time_sec=t_sec,
        fuel_burn_time_min=t_min,
        fuel_burn_time_hr=t_hr,
        rho_kg_m3=rho,
        q_Pa=q,
        CL=CL,
        AR=AR,
        k=k,
        CD=CD,
        drag_N=D,
        fuel_burn_rate_kg_s=fuel_burn_rate,
        V_ms=V,
    )
