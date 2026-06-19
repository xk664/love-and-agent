"""
Health Check API
Comprehensive health monitoring for all services
"""
import asyncio
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from fastapi import APIRouter, status
from pydantic import BaseModel


router = APIRouter(prefix="/internal", tags=["health"])


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class ServiceHealth(BaseModel):
    name: str
    status: HealthStatus
    message: Optional[str] = None
    latency_ms: Optional[float] = None


class HealthResponse(BaseModel):
    status: HealthStatus
    timestamp: datetime
    version: str
    uptime_seconds: float
    services: Dict[str, ServiceHealth]


# Application start time
_start_time = datetime.now()


async def check_database() -> ServiceHealth:
    """Check PostgreSQL database connectivity"""
    try:
        from app.core.config import settings
        import asyncpg

        start = datetime.now()
        conn = await asyncpg.connect(settings.database.DATABASE_URL)
        await conn.execute("SELECT 1")
        await conn.close()
        latency = (datetime.now() - start).total_seconds() * 1000

        return ServiceHealth(
            name="postgresql",
            status=HealthStatus.HEALTHY,
            message="Connected",
            latency_ms=round(latency, 2)
        )
    except Exception as e:
        return ServiceHealth(
            name="postgresql",
            status=HealthStatus.UNHEALTHY,
            message=f"Connection failed: {str(e)[:100]}"
        )


async def check_pgvector() -> ServiceHealth:
    """Check PgVector connectivity"""
    try:
        from app.core.config import settings
        import asyncpg

        start = datetime.now()
        conn = await asyncpg.connect(settings.pgvector.connection_string)
        await conn.execute("SELECT 1")
        await conn.close()
        latency = (datetime.now() - start).total_seconds() * 1000

        return ServiceHealth(
            name="pgvector",
            status=HealthStatus.HEALTHY,
            message="Connected",
            latency_ms=round(latency, 2)
        )
    except Exception as e:
        return ServiceHealth(
            name="pgvector",
            status=HealthStatus.DEGRADED,
            message=f"Connection failed: {str(e)[:100]}"
        )


async def check_redis() -> ServiceHealth:
    """Check Redis connectivity"""
    try:
        from app.core.config import settings
        import redis.asyncio as aioredis

        start = datetime.now()
        redis_client = aioredis.from_url(settings.redis.REDIS_URL)
        await redis_client.ping()
        await redis_client.close()
        latency = (datetime.now() - start).total_seconds() * 1000

        return ServiceHealth(
            name="redis",
            status=HealthStatus.HEALTHY,
            message="Connected",
            latency_ms=round(latency, 2)
        )
    except Exception as e:
        return ServiceHealth(
            name="redis",
            status=HealthStatus.DEGRADED,
            message=f"Connection failed: {str(e)[:100]}"
        )


async def check_dashscope() -> ServiceHealth:
    """Check DashScope API availability"""
    try:
        from app.core.config import settings
        import httpx

        if not settings.dashscope.DASHSCOPE_API_KEY:
            return ServiceHealth(
                name="dashscope",
                status=HealthStatus.DEGRADED,
                message="API key not configured"
            )

        start = datetime.now()
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.dashscope.DASHSCOPE_BASE_URL}/models",
                headers={"Authorization": f"Bearer {settings.dashscope.DASHSCOPE_API_KEY}"},
                timeout=5.0
            )
        latency = (datetime.now() - start).total_seconds() * 1000

        if response.status_code == 200:
            return ServiceHealth(
                name="dashscope",
                status=HealthStatus.HEALTHY,
                message="API available",
                latency_ms=round(latency, 2)
            )
        else:
            return ServiceHealth(
                name="dashscope",
                status=HealthStatus.DEGRADED,
                message=f"API returned status {response.status_code}"
            )
    except Exception as e:
        return ServiceHealth(
            name="dashscope",
            status=HealthStatus.DEGRADED,
            message=f"Connection failed: {str(e)[:100]}"
        )


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Comprehensive health check endpoint.
    Checks all dependent services and returns overall status.
    """
    # Run all health checks concurrently
    checks = await asyncio.gather(
        check_database(),
        check_pgvector(),
        check_redis(),
        check_dashscope(),
        return_exceptions=True
    )

    # Process results
    services = {}
    overall_status = HealthStatus.HEALTHY

    for check in checks:
        if isinstance(check, Exception):
            service = ServiceHealth(
                name="unknown",
                status=HealthStatus.UNHEALTHY,
                message=str(check)[:100]
            )
        else:
            service = check

        services[service.name] = service

        # Update overall status
        if service.status == HealthStatus.UNHEALTHY:
            overall_status = HealthStatus.UNHEALTHY
        elif service.status == HealthStatus.DEGRADED and overall_status != HealthStatus.UNHEALTHY:
            overall_status = HealthStatus.DEGRADED

    # Calculate uptime
    uptime = (datetime.now() - _start_time).total_seconds()

    return HealthResponse(
        status=overall_status,
        timestamp=datetime.now(),
        version="0.1.0",
        uptime_seconds=round(uptime, 2),
        services=services
    )


@router.get("/health/live")
async def liveness_check():
    """
    Simple liveness check for Kubernetes.
    Returns 200 if the application is running.
    """
    return {"status": "alive"}


@router.get("/health/ready")
async def readiness_check():
    """
    Readiness check for Kubernetes.
    Returns 200 if the application is ready to serve traffic.
    """
    # Check critical services only
    db_health = await check_database()

    if db_health.status == HealthStatus.UNHEALTHY:
        return {"status": "not_ready", "reason": "Database unavailable"}, status.HTTP_503_SERVICE_UNAVAILABLE

    return {"status": "ready"}
