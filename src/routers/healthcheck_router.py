# import sqlalchemy as sa
from fastapi import APIRouter
from fastapi.params import Depends
# from redis import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from starlette.responses import JSONResponse

from db.postgres.base import get_async_session
# from db.redis.session_monitor import redis_pool
# from db.s3.s3_aws import get_general_storage

router = APIRouter(tags=["Health check"])


@router.get(
    "/health",
    description="Возвращает статус сервера",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def healthcheck(session: AsyncSession = Depends(get_async_session)):
    errors: list[str] = []
    # DB
    # try:
    #     await session.execute(sa.text("SELECT 1"))
    # except Exception as exc:
    #     errors.append(f"DB: {type(exc).__name__}: {exc}")
    # Redis
    # try:
    #     redis_client = Redis(connection_pool=redis_pool)
    #     redis_client.ping()
    # except Exception as exc:
    #     errors.append(f"Redis: {type(exc).__name__}: {exc}")
    # S3
    # try:
    #     storage = await get_general_storage()
    #     is_ok = await storage.ping()
    #     if not is_ok:
    #         errors.append("S3: endpoint или credentials недоступны")
    # except Exception as exc:
    #     errors.append(f"S3: {type(exc).__name__}: {exc}")

    if errors:
        return JSONResponse({"success": False, "errors": errors}, status_code=status.HTTP_503_SERVICE_UNAVAILABLE)
    return JSONResponse({"success": True}, status_code=status.HTTP_204_NO_CONTENT)
