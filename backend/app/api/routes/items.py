import uuid
from typing import Any

from fastapi import APIRouter

from app.api.deps import CurrentUser, SessionDep
from app.schemas.item import ItemCreate, ItemPublic, ItemsPublic, ItemUpdate
from app.schemas.token import Message
from app.services import item as item_service

router = APIRouter(prefix="/items", tags=["items"])


@router.get("/", response_model=ItemsPublic)
def read_items(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve items.
    """
    return item_service.read_items(
        session=session, current_user=current_user, skip=skip, limit=limit
    )


@router.get("/{id}", response_model=ItemPublic)
def read_item(session: SessionDep, current_user: CurrentUser, id: uuid.UUID) -> Any:
    """
    Get item by ID.
    """
    return item_service.read_item(
        session=session, current_user=current_user, item_id=id
    )


@router.post("/", response_model=ItemPublic)
def create_item(
    *, session: SessionDep, current_user: CurrentUser, item_in: ItemCreate
) -> Any:
    """
    Create new item.
    """
    return item_service.create_item(
        session=session, item_in=item_in, owner_id=current_user.id
    )


@router.put("/{id}", response_model=ItemPublic)
def update_item(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    item_in: ItemUpdate,
) -> Any:
    """
    Update an item.
    """
    return item_service.update_item(
        session=session, current_user=current_user, item_id=id, item_in=item_in
    )


@router.delete("/{id}")
def delete_item(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Message:
    """
    Delete an item.
    """
    item_service.delete_item(session=session, current_user=current_user, item_id=id)
    return Message(message="Item deleted successfully")
