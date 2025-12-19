from fastapi import APIRouter
from pydantic import BaseModel
import math

router = APIRouter(prefix="/isa", tags=["ISA"])


class ISARequest(BaseModel):
    altitude_m: float  # geometric altitude in meters


class ISAResponse(BaseModel):
    altitude_m: float
    temperature_K: float
    pressure_Pa: float
    density_kg_m3: float
    speed_of_sound_m_s: float


# --- ISA constants (up to 11 km troposphere) ---
T0 = 288.15          # K
P0 = 101325.0        # Pa
rho0 = 1.225         # kg/m^3
L = -0.0065          # K/m (lapse rate in troposphere)
g0 = 9.80665         # m/s^2
R = 287.05287        # J/(kg*K)
gamma = 1.4          # air


def isa_tropo(altitude_m: float):
    """
    Simple ISA model for 0–11 km (troposphere).
    For now this is enough for your tools. We can extend to higher layers later.
    """
    h = max(0.0, min(11000.0, altitude_m))  # clamp to 0–11 km

    T = T0 + L * h
    # barometric formula for non-isothermal layer
    exponent = -g0 / (L * R)
    P = P0 * (T / T0) ** exponent
    rho = P / (R * T)
    a = math.sqrt(gamma * R * T)

    return T, P, rho, a


@router.post("/atmosphere", response_model=ISAResponse)
def isa_atmosphere(req: ISARequest):
    """
    ISA atmosphere properties for 0–11 km.
    Input: altitude in meters
    Output: T, P, rho, a
    """
    T, P, rho, a = isa_tropo(req.altitude_m)

    return ISAResponse(
        altitude_m=req.altitude_m,
        temperature_K=T,
        pressure_Pa=P,
        density_kg_m3=rho,
        speed_of_sound_m_s=a,
    )
