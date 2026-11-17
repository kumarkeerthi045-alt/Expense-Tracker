from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models import Expense, User
from ..schemas import ExpenseCreate, ExpenseOut, ExpenseUpdate, Summary

router = APIRouter(prefix="/expenses", tags=["expenses"])


def _get_own_expense(expense_id: int, user: User, db: Session) -> Expense:
    """Fetch an expense, making sure it belongs to the logged-in user."""
    expense = db.get(Expense, expense_id)
    if expense is None or expense.owner_id != user.id:
        # 404 (not 403) so we don't reveal that someone else's record exists
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Expense not found")
    return expense


@router.post("", response_model=ExpenseOut, status_code=status.HTTP_201_CREATED)
def create_expense(
    data: ExpenseCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    expense = Expense(**data.model_dump(), owner_id=user.id)
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense


@router.get("", response_model=list[ExpenseOut])
def list_expenses(
    category: str | None = None,
    start: date | None = Query(None, description="From date (inclusive)"),
    end: date | None = Query(None, description="To date (inclusive)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(Expense).where(Expense.owner_id == user.id)
    if category:
        stmt = stmt.where(Expense.category == category)
    if start:
        stmt = stmt.where(Expense.spent_on >= start)
    if end:
        stmt = stmt.where(Expense.spent_on <= end)
    stmt = stmt.order_by(Expense.spent_on.desc(), Expense.id.desc()).offset(skip).limit(limit)
    return db.scalars(stmt).all()


@router.get("/summary", response_model=Summary)
def summary(
    start: date | None = None,
    end: date | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = (
        select(Expense.category, func.sum(Expense.amount), func.count(Expense.id))
        .where(Expense.owner_id == user.id)
        .group_by(Expense.category)
    )
    if start:
        stmt = stmt.where(Expense.spent_on >= start)
    if end:
        stmt = stmt.where(Expense.spent_on <= end)
    rows = db.execute(stmt).all()
    by_category = {cat: round(total, 2) for cat, total, _ in rows}
    return Summary(
        total=round(sum(by_category.values()), 2),
        count=sum(c for _, _, c in rows),
        by_category=by_category,
    )


@router.get("/{expense_id}", response_model=ExpenseOut)
def get_expense(
    expense_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    return _get_own_expense(expense_id, user, db)


@router.patch("/{expense_id}", response_model=ExpenseOut)
def update_expense(
    expense_id: int,
    data: ExpenseUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    expense = _get_own_expense(expense_id, user, db)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(expense, field, value)
    db.commit()
    db.refresh(expense)
    return expense


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(
    expense_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    expense = _get_own_expense(expense_id, user, db)
    db.delete(expense)
    db.commit()
