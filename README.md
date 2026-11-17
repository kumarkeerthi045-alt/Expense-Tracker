# 💸 Expense Tracker API

A secure REST API to track personal expenses, built with **FastAPI**, **SQLAlchemy** and **JWT authentication**.
Users register, log in, and manage only their own expenses, with filtering by category and date plus a category-wise spending summary.

![Python](https://img.shields.io/badge/Python-3.10+-blue) ![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green) ![Tests](https://img.shields.io/badge/tests-pytest-orange)

## ✨ Features

- **User accounts**: register and log in, passwords hashed with **bcrypt**
- **JWT auth**: every expense route needs a valid bearer token
- **Full CRUD** on expenses (create, read, update with PATCH, delete)
- **Filters**: by category, date range, plus pagination (`skip`, `limit`)
- **Summary endpoint**: total spend, count, and breakdown per category
- **Data isolation**: a user can never read or delete another user's data
- **Input validation**: amount must be positive, category must be from a fixed list
- **Auto-generated docs** at `/docs` (Swagger UI)
- **8 automated tests** + GitHub Actions CI

## 🏗️ Project Structure

```
app/
├── main.py          # App entry point, registers routers
├── database.py      # DB engine + session dependency
├── models.py        # SQLAlchemy tables: User, Expense
├── schemas.py       # Pydantic request/response models + validation
├── auth.py          # bcrypt hashing, JWT create/verify, current-user dependency
└── routers/
    ├── auth.py      # /auth/register, /auth/login, /auth/me
    └── expenses.py  # /expenses CRUD, filters, /expenses/summary
tests/test_api.py    # End-to-end API tests (in-memory DB)
```

## 🚀 Run It Locally

**Needs:** Python 3.10 or newer ([download](https://www.python.org/downloads/)). Works on Windows, Mac and Linux.

```bash
# 1. Go into the project folder
cd expense-tracker-api

# 2. Create a virtual environment and activate it
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac / Linux

# 3. Install packages
pip install -r requirements-dev.txt

# 4. Start the server
uvicorn app.main:app --reload
```

Open **http://127.0.0.1:8000/docs** in your browser. You can test every endpoint from there:
1. `POST /auth/register` → create an account
2. Click the **Authorize 🔒** button (top right) → enter your email + password
3. Now try `POST /expenses`, `GET /expenses`, `GET /expenses/summary`

**Run the tests:**
```bash
pytest -q
```

## 📡 API Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/auth/register` | Create account | ❌ |
| POST | `/auth/login` | Get JWT token | ❌ |
| GET | `/auth/me` | Current user | ✅ |
| POST | `/expenses` | Add expense | ✅ |
| GET | `/expenses?category=food&start=2026-10-01&end=2026-10-31` | List with filters | ✅ |
| GET | `/expenses/summary` | Totals by category | ✅ |
| GET | `/expenses/{id}` | One expense | ✅ |
| PATCH | `/expenses/{id}` | Update some fields | ✅ |
| DELETE | `/expenses/{id}` | Delete | ✅ |

**Example request body:**
```json
{ "title": "Lunch", "amount": 180, "category": "food", "spent_on": "2026-11-01" }
```
Categories: `food, travel, rent, shopping, bills, health, other`

## 🔐 Configuration

Copy `.env.example` → set these as environment variables:

| Variable | Default | Purpose |
|----------|---------|---------|
| `SECRET_KEY` | dev key | Signs JWT tokens. **Change in production.** |
| `DATABASE_URL` | `sqlite:///./expenses.db` | Any SQLAlchemy URL (e.g. PostgreSQL) |
| `TOKEN_EXPIRE_MINUTES` | `60` | Token lifetime |

## 🧠 Design Decisions

- **404 instead of 403** when accessing someone else's expense, so the API doesn't reveal that the record exists.
- **PATCH with `exclude_unset`**: only fields the client actually sent are changed.
- **Dependency injection** (`Depends(get_db)`, `Depends(get_current_user)`) keeps routes clean and makes testing easy: tests swap in an in-memory database.
- **SQL aggregation** (`GROUP BY` + `SUM`) for the summary is done in the database, not in Python loops.

## 🔮 Future Improvements

- Monthly budgets with alerts
- CSV export
- Alembic migrations + PostgreSQL in Docker
- Refresh tokens

## 📄 License
MIT


## 🖥️ Web Dashboard

A responsive browser dashboard is included in `static/` and served by FastAPI:
- Open `http://127.0.0.1:8000/` for the Pennywise dashboard.
- Open `http://127.0.0.1:8000/docs` for the interactive API documentation.
- Register or sign in from the dashboard. Expenses are saved through the existing authenticated API.
