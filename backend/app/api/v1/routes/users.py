from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models import User
from app.schemas import UserUpdateRequest
from app.services import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.patch("/{user_id}", summary="Update profile settings")
async def update_user(
    user_id: str,
    request: UserUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot update another user")
    service = UserService(db)
    return service.update_user(user_id, request.full_name)


@router.get("/{user_id}/export", summary="Export user data")
async def export_user_data(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot export another user's data")
    service = UserService(db)
    return service.export_user_data(user_id)
