"""Pydantic schemas: validate what comes in and shape what goes out."""
from datetime import date

from pydantic import BaseModel, ConfigDict, EmailStr, Field

CATEGORIES = ["food", "travel", "rent", "shopping", "bills", "health", "other"]


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=72)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: EmailStr


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ExpenseBase(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    amount: float = Field(gt=0, description="Amount in rupees, must be positive")
    category: str = Field(default="other", pattern="^(" + "|".join(CATEGORIES) + ")$")
    spent_on: date = Field(default_factory=date.today)


class ExpenseCreate(ExpenseBase):
    pass


class ExpenseUpdate(BaseModel):
    """All fields optional so the client can update just one field (PATCH)."""
    title: str | None = Field(default=None, min_length=1, max_length=120)
    amount: float | None = Field(default=None, gt=0)
    category: str | None = Field(default=None, pattern="^(" + "|".join(CATEGORIES) + ")$")
    spent_on: date | None = None


class ExpenseOut(ExpenseBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class Summary(BaseModel):
    total: float
    count: int
    by_category: dict[str, float]
