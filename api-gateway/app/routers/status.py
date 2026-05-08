from fastapi import APIRouter
from app.schemas.openapi import CrawlerStatusResponse, AnalysisStatusResponse
from datetime import datetime, timezone
import redis
from app.config import get_settings

router = APIRouter(prefix="/api/v1", tags=["Status"])

settings = get_settings()


@router.get("/crawler/status", response_model=CrawlerStatusResponse)
async def get_crawler_status():
    try:
        r = redis.from_url(settings.redis_url)
        queue_size = r.llen("crawl_tasks") if r.exists("crawl_tasks") else 0
        r.close()
    except Exception:
        queue_size = 0

    return CrawlerStatusResponse(
        status="running" if queue_size >= 0 else "stopped",
        active_spiders=4,
        pages_crawled_today=0,
        items_extracted_today=0,
        last_crawl=datetime.now(timezone.utc),
        queue_size=queue_size,
    )


@router.get("/analysis/status", response_model=AnalysisStatusResponse)
async def get_analysis_status():
    try:
        r = redis.from_url(settings.redis_url)
        pending = r.llen("analysis_tasks") if r.exists("analysis_tasks") else 0
        r.close()
    except Exception:
        pending = 0

    return AnalysisStatusResponse(
        status="running",
        pending_tasks=pending,
        processed_today=0,
        trends_identified_today=0,
        last_processed=datetime.now(timezone.utc),
        worker_count=2,
    )
