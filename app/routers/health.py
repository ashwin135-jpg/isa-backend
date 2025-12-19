from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/ping")
def ping():
    return {"status": "ok", "message": "ISA backend alive"}


@router.get("/")
def root():
    return {"message": "ISA Backend is running"}
