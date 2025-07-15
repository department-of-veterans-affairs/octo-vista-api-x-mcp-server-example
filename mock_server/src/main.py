"""
Vista API X Mock Server - Main Application
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.auth.resource import auth_router
from src.config import get_settings
from src.database.dynamodb_client import get_dynamodb_client
from src.exceptions.handlers import (
    FoundationsException,
    JwtException,
    RpcFaultException,
    SecurityFaultException,
    VistaLinkFaultException,
    foundations_exception_handler,
    http_exception_handler,
    jwt_exception_handler,
    rpc_fault_handler,
    security_fault_handler,
    vistalink_fault_handler,
)
from src.middleware.auth_filter import VistaApiXAuthenticationFilter
from src.rpc.resource import rpc_router

# Get settings instance
settings = get_settings()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info(f"Starting Vista API X Mock Server version {settings.app_version}")

    # Initialize DynamoDB if in development
    if settings.environment == "development":
        try:
            db_client = get_dynamodb_client()
            await db_client.seed_test_data()
            logger.info("Test data seeded successfully")
        except Exception as e:
            logger.warning(f"Failed to seed test data: {e}")

    yield

    # Shutdown
    logger.info("Shutting down Vista API X Mock Server")


# Create main application
app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)

# Create Vista API X sub-application
vista_app = FastAPI(
    title="Vista API X",
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Add CORS middleware
vista_app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=settings.cors_allowed_methods,
    allow_headers=settings.cors_allowed_headers,
)

# Add authentication middleware
vista_app.add_middleware(VistaApiXAuthenticationFilter)

# Register routers
vista_app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
vista_app.include_router(rpc_router, prefix="/vista-sites", tags=["RPC"])

# Register exception handlers
vista_app.add_exception_handler(VistaLinkFaultException, vistalink_fault_handler)
vista_app.add_exception_handler(SecurityFaultException, security_fault_handler)
vista_app.add_exception_handler(RpcFaultException, rpc_fault_handler)
vista_app.add_exception_handler(JwtException, jwt_exception_handler)
vista_app.add_exception_handler(FoundationsException, foundations_exception_handler)
vista_app.add_exception_handler(Exception, http_exception_handler)

# Mount vista_app under /vista-api-x for production path parity
app.mount("/vista-api-x", vista_app)


@app.get("/health")
async def health():
    """Health check endpoint"""
    try:
        db_client = get_dynamodb_client()
        await db_client.get_application_by_key("health-check")
        db_status = "healthy"
    except Exception as e:
        logger.error(f"DynamoDB health check failed: {e}")
        db_status = "unhealthy"

    return {
        "status": "healthy",
        "version": settings.app_version,
        "environment": settings.environment,
        "dependencies": {"dynamodb": db_status},
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=settings.server_port,
        log_level=settings.log_level.lower(),
        reload=True,
    )
