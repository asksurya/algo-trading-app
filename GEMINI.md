# GEMINI.md

## Project Overview

This is a comprehensive algorithmic trading platform designed for backtesting and live trading strategies using the Alpaca API. The system is composed of a modern web application architecture with a Python backend and a Next.js frontend, plus a Streamlit dashboard for quick analysis.

**Core Components:**

*   **Backend API:** Python (FastAPI) service handling business logic, data management, authentication, and trading execution.
*   **Web Frontend:** Next.js (TypeScript) application providing the primary user interface for dashboarding, strategy management, and monitoring.
*   **Data Analysis Dashboard:** Streamlit application for interactive data visualization and rapid prototyping.
*   **Infrastructure:** Dockerized services including PostgreSQL (database) and Redis (caching/messaging).

## Technology Stack

*   **Backend:**
    *   **Language:** Python 3.11+
    *   **Framework:** FastAPI
    *   **ORM:** SQLAlchemy 2.0 (Async)
    *   **Database:** PostgreSQL 15+
    *   **Caching:** Redis 7+
    *   **Trading API:** Alpaca Markets (via `alpaca-py` or direct API)
    *   **Testing:** Pytest
    *   **Package Manager:** Poetry (implied by `pyproject.toml`) or pip (`requirements.txt`)

*   **Frontend:**
    *   **Framework:** Next.js 14 (App Router)
    *   **Language:** TypeScript
    *   **Styling:** Tailwind CSS, shadcn/ui
    *   **State Management:** Zustand (Client), React Query (Server)
    *   **Real-time:** Socket.IO / WebSockets

*   **DevOps:**
    *   **Containerization:** Docker & Docker Compose

## Building and Running

### Docker (Recommended)

The entire stack (Database, Redis, Backend, Frontend) can be launched using Docker Compose.

1.  **Build and Start:**
    ```bash
    docker-compose up --build
    ```
2.  **Access Services:**
    *   **Frontend:** `http://localhost:3002`
    *   **Backend API:** `http://localhost:8000`
    *   **API Documentation:** `http://localhost:8000/docs` or `http://localhost:8000/redoc`

### Local Development

**Backend:**
1.  Navigate to `backend/`.
2.  Install dependencies: `poetry install` or `pip install -r requirements.txt`.
3.  Set up `.env` (copy `.env.example`).
4.  Run server: `uvicorn app.main:app --reload` (or via `poetry run`).

**Frontend:**
1.  Navigate to `frontend/`.
2.  Install dependencies: `npm install`.
3.  Set up `.env.local` (copy `.env.local.example`).
4.  Run server: `npm run dev`.
5.  Access at `http://localhost:3000`.

**Streamlit Dashboard:**
1.  Install dependencies (likely in root `requirements.txt`).
2.  Run: `streamlit run app.py` (or `pages/*.py`).

## Project Structure

*   `backend/`: FastAPI application source code.
    *   `app/`: Main application package (API routes, models, schemas, services).
    *   `tests/`: Pytest suite.
    *   `alembic/` or `migrations/`: Database migration scripts.
*   `frontend/`: Next.js application source code.
    *   `src/app/`: App Router pages and layouts.
    *   `src/components/`: Reusable UI components.
    *   `src/lib/`: Utilities, API clients, and hooks.
*   `models/`: Likely shared or specific ML/Strategy models (check contents).
*   `data/`: Local storage for SQLite dbs or flat files (if applicable).
*   `docker-compose.yml`: Orchestration for the full stack.

## Development Conventions

*   **Code Style:**
    *   **Python:** Follows PEP 8. Uses `black` for formatting, `isort` for imports, and `mypy` for type checking.
    *   **TypeScript:** Standard Prettier/ESLint configuration.
*   **Configuration:** Environment variables are used for sensitive data (API keys, DB credentials). **Never** commit `.env` files.
*   **Testing:**
    *   Backend tests are in `backend/tests`.
    *   Frontend tests use `jest` and `playwright` (e2e).
*   **API Integration:** Frontend communicates with Backend via REST (axios) and potentially WebSockets for live data.

## Key Commands

*   **Backend Format/Lint:** `black .`, `isort .`, `flake8`, `mypy .`
*   **Frontend Lint:** `npm run lint`
*   **Run Tests:** `pytest` (Backend), `npm test` (Frontend)
