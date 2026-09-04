from fastapi import APIRouter, Depends

from app.api.deps import require_role
from app.models.enums import UserRole
from app.models.user import User

router = APIRouter(tags=["Organizer"])


@router.get("/organizer/ping")
def organizer_ping(
    current_user: User = Depends(
        require_role(
            UserRole.ORGANIZER,
            UserRole.ADMIN,
        )
    )
):
    return {
        "message": f"Hello {current_user.email}"
    }

from datetime import datetime
from fastapi import APIRouter, Header

from app.core.redis_client import async_redis_client
from app.core.idempotency import (
    check_and_store_idempotency,
    store_idempotent_result,
)



@router.post("/test-idempotent")
async def test_idempotent_route(
    idempotency_key: str = Header(...)
):
    is_duplicate, stored = await check_and_store_idempotency(
        async_redis_client,
        idempotency_key
    )

    if is_duplicate:
        return {
            "duplicate": True,
            "result": stored
        }

    result = {
        "processed_at": datetime.utcnow().isoformat(),
        "message": "did the thing"
    }

    await store_idempotent_result(
        async_redis_client,
        idempotency_key,
        result
    )

    return {
        "duplicate": False,
        "result": result
    }


