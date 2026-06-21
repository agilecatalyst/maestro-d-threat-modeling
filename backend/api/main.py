from contextlib import asynccontextmanager
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from database import SessionLocal, run_migrations
from routes import admin, diagrams, threat_models
from security import parse_cors_origins


@asynccontextmanager
async def lifespan(app: FastAPI):
    run_migrations()
    yield


app = FastAPI(title="Maestro'D API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=parse_cors_origins(os.getenv("CORS_ORIGINS")),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "service": "maestro-d-api",
            "database": "connected",
        }
    except SQLAlchemyError:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "service": "maestro-d-api",
                "database": "disconnected",
            },
        )
    finally:
        db.close()


app.include_router(diagrams.router)
app.include_router(threat_models.router)
app.include_router(admin.router)
