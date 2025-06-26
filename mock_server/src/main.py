"""
Vista API X Mock Server - Main Application
"""

import asyncio
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.auth.resource import auth_router
from src.config import settings
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

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting Vista API X Mock Server", version=settings.app_version)

    # Initialize DynamoDB
    if settings.environment == "development":
        logger.info("Seeding test data in DynamoDB")
        db_client = get_dynamodb_client()
        try:
            await db_client.seed_test_data()
            logger.info("Test data seeded successfully")
        except Exception as e:
            logger.error("Failed to seed test data", error=str(e))

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


# Add root endpoint for vista-api-x
@vista_app.get("/")
async def vista_api_root():
    """Vista API X root endpoint"""
    return {
        "service": "Vista API X Mock",
        "version": settings.app_version,
        "status": "healthy",
        "endpoints": [
            "POST /auth/token - Get JWT token",
            "POST /auth/refresh - Refresh JWT token",
            "POST /vista-sites/{station_number}/users/{caller_duz}/rpc/invoke - Execute RPC",
        ],
        "documentation": {
            "openapi": "/openapi.json",
            "docs": "/docs",
            "redoc": "/redoc",
        },
    }


# Register exception handlers
vista_app.add_exception_handler(VistaLinkFaultException, vistalink_fault_handler)
vista_app.add_exception_handler(SecurityFaultException, security_fault_handler)
vista_app.add_exception_handler(RpcFaultException, rpc_fault_handler)
vista_app.add_exception_handler(JwtException, jwt_exception_handler)
vista_app.add_exception_handler(FoundationsException, foundations_exception_handler)
vista_app.add_exception_handler(Exception, http_exception_handler)

# Replace the main app with vista_app to match production paths
app = vista_app


@app.get("/health")
async def health():
    """Health check endpoint"""
    # Check DynamoDB connectivity
    db_status = "healthy"
    try:
        db_client = get_dynamodb_client()
        # Try a simple operation
        await db_client.get_application_by_key("health-check")
    except Exception as e:
        db_status = f"unhealthy: {e!s}"

    return {
        "status": "healthy",
        "version": settings.app_version,
        "environment": settings.environment,
        "dependencies": {"dynamodb": db_status},
    }


# Health check server on separate port
health_app = FastAPI()


@health_app.get("/health")
async def health_check():
    """Health check for load balancer"""
    return {"status": "healthy"}


async def run_servers():
    """Run both main and health check servers concurrently"""
    import uvicorn

    # Main app config
    main_config = uvicorn.Config(
        "src.main:app",
        host="0.0.0.0",
        port=settings.server_port,
        log_level=settings.log_level.lower(),
        access_log=True,
    )
    main_server = uvicorn.Server(main_config)

    # Health check app config
    health_config = uvicorn.Config(
        "src.main:health_app",
        host="0.0.0.0",
        port=settings.health_check_port,
        log_level="warning",
    )
    health_server = uvicorn.Server(health_config)

    # Run both servers concurrently
    await asyncio.gather(main_server.serve(), health_server.serve())


def run():
    """Run the application"""
    asyncio.run(run_servers())


if __name__ == "__main__":
    run()
