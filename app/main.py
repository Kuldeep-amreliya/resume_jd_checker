"""
FastAPI app entrypoint.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database.session import init_db
from app.api.routes_match import router as match_router

# -------------------------------------------------------------------
# Logging Configuration
# -------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)

settings = get_settings()


# -------------------------------------------------------------------
# Application Lifespan
# -------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 60)
    logger.info("Starting Resume JD Checker API...")
    logger.info("Application Name : %s", settings.app_name)

    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized successfully.")

    logger.info("Application startup completed.")
    logger.info("=" * 60)

    yield

    logger.info("=" * 60)
    logger.info("Shutting down Resume JD Checker API...")
    logger.info("Application shutdown completed.")
    logger.info("=" * 60)


# -------------------------------------------------------------------
# FastAPI App
# -------------------------------------------------------------------

app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan,
)

# -------------------------------------------------------------------
# Middleware
# -------------------------------------------------------------------

logger.info("Configuring CORS middleware...")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info("CORS middleware configured.")

# -------------------------------------------------------------------
# Routers
# -------------------------------------------------------------------

logger.info("Registering API routes...")

app.include_router(match_router)

logger.info("API routes registered successfully.")

# -------------------------------------------------------------------
# Root Endpoint
# -------------------------------------------------------------------

@app.get("/")
def root():
    logger.info("Health check endpoint '/' accessed.")
    return {
        "app": settings.app_name,
        "status": "running",
    }