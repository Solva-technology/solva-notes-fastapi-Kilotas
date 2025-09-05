from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/ping", summary="Liveness probe")
async def ping():
    return {"status": "ok"}
