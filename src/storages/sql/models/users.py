__all__ = ["User", "InnopolisSSOUser"]

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import relationship, mapped_column, Mapped
from sqlalchemy.types import ARRAY

from src.storages.sql.__mixin__ import IdMixin, UpdateCreateDateTimeMixin
from src.storages.sql.models.base import Base


class User(Base, IdMixin):
    __ownerships_tables__ = dict()
    __tablename__ = "users"

    innopolis_sso: Mapped["InnopolisSSOUser"] = relationship(
        "InnopolisSSOUser",
        uselist=False,
        lazy="joined",
        back_populates="user",
    )


class InnopolisSSOUser(Base, UpdateCreateDateTimeMixin):
    __tablename__ = "innopolis_sso_users"

    id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    user: Mapped[User] = relationship("User", back_populates="innopolis_sso")

    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    # may be many statuses, default is empty list
    status: Mapped[list[str]] = mapped_column(
        ARRAY(String(255)), nullable=False, server_default="{}"
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    access_token: Mapped[str] = mapped_column(Text(), nullable=False)
    refresh_token: Mapped[str] = mapped_column(Text(), nullable=False)
