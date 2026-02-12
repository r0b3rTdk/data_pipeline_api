"""
User repository.

Handles retrieval of internal user accounts.
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infra.db.models.user_account import UserAccount

def get_user_by_username(db: Session, username: str) -> UserAccount | None:
    # Retorna um usuario pelo nome
    stmt = select(UserAccount).where(UserAccount.username == username)
    return db.execute(stmt).scalars().first()


def get_user_by_id(db: Session, user_id: int) -> UserAccount | None:
    # Retorna um usuario pelo ID
    stmt = select(UserAccount).where(UserAccount.id == user_id)
    return db.execute(stmt).scalars().first()