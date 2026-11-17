"""Entry point. Run with: uvicorn app.main:app --reload"""
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .database import Base, engine
from .routers import auth, expenses

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Expense Tracker API",
    description="Track personal expenses with secure JWT login, filters and monthly summaries.",
    version="1.0.0",
)

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

app.include_router(auth.router)
app.include_router(expenses.router)


@app.get("/", include_in_schema=False)
def frontend():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok", "docs": "/docs"}
