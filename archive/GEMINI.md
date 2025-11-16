# GEMINI.md

## Project Overview

This is a comprehensive algorithmic trading platform with a multi-faceted architecture. It supports backtesting and live trading of various strategies using the Alpaca API. The project is composed of a Python backend, a Next.js web application, and a Streamlit dashboard.

**Core Technologies:**

*   **Backend:** Python with FastAPI, SQLAlchemy for database interaction, and `alpaca-py` for trading.
*   **Frontend (Web App):** Next.js with TypeScript, React, `react-query` for data fetching, `zustand` for state management, `recharts` for charting, and `tailwindcss` for styling.
*   **Frontend (Dashboard):** Streamlit with Plotly for quick data analysis and visualization.
*   **Database:** PostgreSQL for data storage.
*   **Cache:** Redis for caching.
*   **Deployment:** The project is containerized using Docker and can be deployed to various cloud platforms.

## Building and Running

### Docker (Recommended)

The most straightforward way to run the entire application stack is by using Docker Compose.

1.  **Build and run the services:**

    ```bash
    docker-compose up --build
    ```

2.  **Access the services:**
    *   **Backend API:** `http://localhost:8000`
    *   **Backend API Docs:** `http://localhost:8000/docs`
    *   **Frontend Web App:** `http://localhost:3002`

### Local Development

**Backend (FastAPI):**

1.  **Navigate to the backend directory:**

    ```bash
    cd backend
    ```

2.  **Install dependencies:**

    ```bash
    pip install -r ../requirements.txt
    ```

3.  **Run the development server:**

    ```bash
    uvicorn app.main:app --reload
    ```

**Frontend (Next.js):**

1.  **Navigate to the frontend directory:**

    ```bash
    cd frontend
    ```

2.  **Install dependencies:**

    ```bash
    npm install
    ```

3.  **Run the development server:**

    ```bash
    npm run dev
    ```

**Streamlit Dashboard:**

1.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

2.  **Run the Streamlit app:**

    ```bash
    streamlit run app.py
    ```

### Command-Line Interface

The project also provides a command-line interface for backtesting and live trading.

*   **Backtesting:**

    ```bash
    python main.py backtest --strategy sma --symbol AAPL --start-date 2023-01-01 --end-date 2024-01-01
    ```

*   **Live Trading:**

    ```bash
    python main.py live --strategy sma --symbols AAPL,TSLA --paper
    ```

## Development Conventions

*   **Code Style:** The Python code appears to follow the `black` code style. The presence of `flake8` and `mypy` in the `requirements.txt` file suggests a commitment to code quality and type safety.
*   **Testing:** The project includes a `tests` directory in the backend, indicating the use of `pytest` for unit and integration testing.
*   **API Documentation:** The backend API is documented using OpenAPI (Swagger) and ReDoc, available at `/docs` and `/redoc` respectively.
*   **Deployment:** The project is designed for containerized deployments using Docker. The `DEPLOYMENT_GUIDE.md` file provides detailed instructions for deploying to various cloud providers.
*   **Modularity:** The project is well-structured, with clear separation between the backend, frontend, and core trading logic. This modular design makes it easier to maintain and extend the application.
