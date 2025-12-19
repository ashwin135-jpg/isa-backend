from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import mach, fuel_range, lift_drag, mission_planner

app = FastAPI(
    title="ISA Master Tool API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "message": "ISA Backend is running",
        "docs_url": "/docs",
        "health_url": "/api/health",
    }


@app.get("/api/health")
def health():
    return {"message": "ISA Backend is running"}


@app.get("/api/isa")
def isa_endpoint(altitude_m: float):
    T0 = 288.15       # K
    L = -0.0065       # K/m
    p0 = 101325.0     # Pa
    R = 287.058       # J/(kg·K)
    g = 9.80665       # m/s^2
    gamma = 1.4

    T = T0 + L * altitude_m
    p = p0 * (T / T0) ** (-g / (L * R))
    rho = p / (R * T)
    a = (gamma * R * T) ** 0.5  # speed of sound [m/s]

    return {
        "altitude_m": altitude_m,
        "temperature_K": T,
        "pressure_Pa": p,
        "density_kg_m3": rho,
        "speed_of_sound_m_s": a,
    }


# ---- Routers for the tools ----
# Final endpoints exposed:
#   POST /api/mach/compute
#   POST /api/fuel-range/estimate
#   POST /api/lift-drag/compute        (assuming your lift_drag router defines this)
#   POST /api/mission-planner/estimate
app.include_router(mach.router, prefix="/api")
app.include_router(fuel_range.router, prefix="/api")
app.include_router(lift_drag.router, prefix="/api")
app.include_router(mission_planner.router, prefix="/api")
