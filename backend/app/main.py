from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from app.core.config import get_settings, INSECURE_DEV_SECRETS
from app.api.routes import router as api_router
from app.api.ai_routes import router as ai_router
from app.api.risk_routes import router as risk_router
from app.api.logistics_advisor_routes import router as logistics_advisor_router
from app.api.auth_routes import router as auth_router
from app.api.forecasting_routes import router as forecasting_router
from app.api.dispatch_routes import router as dispatch_router
from app.api.operational_routes import router as operational_router
from app.core.database import engine, Base, init_db
import app.models.domain  # noqa: F401

from contextlib import asynccontextmanager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("reliefos")

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Production security validation
    if settings.is_production:
        try:
            secret = settings.get_jwt_secret()
            if secret in INSECURE_DEV_SECRETS or len(secret) < 32:
                raise RuntimeError(
                    "CRITICAL SECURITY CONFIGURATION ERROR: Production deployment requires a secure, "
                    "cryptographically random JWT_SECRET of at least 32 characters. Do not use development defaults."
                )
        except Exception as e:
            raise RuntimeError(
                f"CRITICAL SECURITY CONFIGURATION ERROR: Safe production startup aborted: {e}"
            )
        if not settings.AUTH_STRICT:
            logger.warning("AUTH_STRICT was False in production mode. Auto-enforcing AUTH_STRICT=True.")
            settings.AUTH_STRICT = True

        if not settings.is_postgres:
            raise RuntimeError(
                "CRITICAL DATABASE CONFIGURATION ERROR: Production deployment requires a PostgreSQL database. "
                "SQLite is only supported in development and test environments."
            )

    try:
        init_db()
        logger.info(f"Database tables initialized and seeded successfully ({settings.database_engine_type}).")
    except Exception as exc:
        if settings.is_postgres:
            logger.error(
                f"PostgreSQL connection failed during startup: {exc}. "
                "Ensure PostgreSQL daemon is running and credentials in DATABASE_URL are reachable."
            )
            if not settings.DEBUG:
                raise RuntimeError(f"Database initialization failed in production: {exc}")
        else:
            raise
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="RELIEFOS Lite — Real-Time Flood Monitoring & Disaster Relief Resource Optimization Engine",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS for React frontend (port 3012) - strictly without insecure wildcard credentials
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred in the disaster relief engine.",
            "path": request.url.path
        },
    )


@app.get("/", tags=["Root"])
async def root():
    return {
        "system": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "region": "Kamrup Metropolitan & Assam Operational Grid (9 Monitored Districts)",
        "jurisdiction": "Assam State Disaster Management Authority (ASDMA)",
        "status": "online",
        "documentation": "/docs",
        "health_check": "/api/health"
    }


# Include all modular API endpoints under /api
app.include_router(api_router, prefix="/api")
app.include_router(ai_router, prefix="/api")
app.include_router(risk_router, prefix="/api")
app.include_router(logistics_advisor_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(forecasting_router, prefix="/api")
app.include_router(dispatch_router, prefix="/api")
app.include_router(operational_router, prefix="/api")

