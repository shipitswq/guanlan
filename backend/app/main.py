from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db
from app.routers import agents, stocks

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    print("Database initialized")
    # Preload stock list on startup for faster search
    try:
        from app.services.data_fetcher import DataFetcher
        f = DataFetcher()
        await f.preload_stocks()
        print("Stock list preloaded")
    except Exception as e:
        print(f"Stock list preload skipped: {e}")
    yield

app = FastAPI(title="A-Share Simulation Trader", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agents.router)
app.include_router(stocks.router)

@app.get("/api/health")
async def health():
    return {"status": "ok"}
