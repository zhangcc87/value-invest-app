from typing import Any

from fastapi import APIRouter

from app.api.deps import SessionDep
from app.schemas.user import PrivateUserCreate, UserPublic
from app.services import user as user_service

router = APIRouter(tags=["private"], prefix="/private")


@router.post("/users/", response_model=UserPublic)
def create_user(user_in: PrivateUserCreate, session: SessionDep) -> Any:
    """
    Create a new user.
    """
    return user_service.create_user_private(session=session, user_in=user_in)
