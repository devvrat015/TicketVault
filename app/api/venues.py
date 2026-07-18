from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.enums import UserRole
from app.api.deps import require_role
from app.models.user import User
from app.models.venue import Venue
from app.schemas.venue import VenueCreate, VenueOut

router = APIRouter(
    prefix="/venues",
    tags=["Venues"]
)


@router.post(
    "/",
    response_model=VenueOut,
    status_code=status.HTTP_201_CREATED,
)
def create_venue(
    venue: VenueCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(UserRole.ADMIN)
    ),
):
    new_venue = Venue(
        name=venue.name,
        city=venue.city,
        address=venue.address,
    )

    db.add(new_venue)
    db.commit()
    db.refresh(new_venue)

    return new_venue


@router.get(
    "/",
    response_model=list[VenueOut],
)
def get_all_venues(
    db: Session = Depends(get_db),
):
    venues = db.query(Venue).all()
    return venues


@router.get(
    "/{venue_id}",
    response_model=VenueOut,
)
def get_venue(
    venue_id: int,
    db: Session = Depends(get_db),
):
    venue = db.query(Venue).filter(Venue.id == venue_id).first()

    if venue is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Venue not found",
        )

    return venue