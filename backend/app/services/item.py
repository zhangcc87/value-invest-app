import uuid

from fastapi import HTTPException
from sqlmodel import Session

from app.models import Item, User
from app.repositories import item as item_repo
from app.schemas.item import ItemCreate, ItemPublic, ItemsPublic, ItemUpdate


def create_item(*, session: Session, item_in: ItemCreate, owner_id: uuid.UUID) -> Item:
    db_item = Item.model_validate(item_in, update={"owner_id": owner_id})
    item_repo.add(session=session, item=db_item)
    session.commit()
    session.refresh(db_item)
    return db_item


def read_items(
    *, session: Session, current_user: User, skip: int, limit: int
) -> ItemsPublic:
    if current_user.is_superuser:
        count = item_repo.count_items(session=session)
        items = item_repo.list_items(session=session, skip=skip, limit=limit)
    else:
        count = item_repo.count_items_by_owner(
            session=session, owner_id=current_user.id
        )
        items = item_repo.list_items_by_owner(
            session=session, owner_id=current_user.id, skip=skip, limit=limit
        )

    items_public = [ItemPublic.model_validate(item) for item in items]
    return ItemsPublic(data=items_public, count=count)


def read_item(*, session: Session, current_user: User, item_id: uuid.UUID) -> Item:
    item = item_repo.get_item_by_id(session=session, item_id=item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if not current_user.is_superuser and (item.owner_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return item


def update_item(
    *,
    session: Session,
    current_user: User,
    item_id: uuid.UUID,
    item_in: ItemUpdate,
) -> Item:
    item = read_item(session=session, current_user=current_user, item_id=item_id)
    update_dict = item_in.model_dump(exclude_unset=True)
    item.sqlmodel_update(update_dict)
    item_repo.add(session=session, item=item)
    session.commit()
    session.refresh(item)
    return item


def delete_item(*, session: Session, current_user: User, item_id: uuid.UUID) -> None:
    item = read_item(session=session, current_user=current_user, item_id=item_id)
    item_repo.delete(session=session, item=item)
    session.commit()
