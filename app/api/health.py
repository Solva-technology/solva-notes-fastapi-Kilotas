from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

router = APIRouter(tags=["health"])


@router.get("/ping", summary="Liveness probe")
async def ping():
    # только факт, что процесс жив
    return {"status": "ok"}
