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