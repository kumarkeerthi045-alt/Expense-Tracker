"""Database tables (ORM models)."""
from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    expenses: Mapped[list["Expense"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )


class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(120))
    amount: Mapped[float] = mapped_column(Float)
    category: Mapped[str] = mapped_column(String(50), index=True)
    spent_on: Mapped[date] = mapped_column(Date, default=date.today)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    owner: Mapped[User] = relationship(back_populates="expenses")
