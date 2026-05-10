import time
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.repositories.analytics_repo import AnalyticsRepository
from app.schemas.openapi import (
    CrawlerSourceSummary, DataLayerSummary,
    BotUsageSummary, AnalyticsConfigSummary, BotUsageLogRequest,
)
from typing import List

router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics"])


@router.get("/crawler/summary", response_model=List[CrawlerSourceSummary])
async def get_crawler_summary(db: AsyncSession = Depends(get_db)):
    repo = AnalyticsRepository(db)
    return await repo.get_crawler_source_summary()


@router.get("/data/summary", response_model=DataLayerSummary)
async def get_data_summary(db: AsyncSession = Depends(get_db)):
    repo = AnalyticsRepository(db)
    return await repo.get_data_layer_summary()


@router.get("/bot/usage", response_model=BotUsageSummary)
async def get_bot_usage(db: AsyncSession = Depends(get_db)):
    repo = AnalyticsRepository(db)
    return await repo.get_bot_usage_summary()


@router.post("/bot/log", status_code=201)
async def log_bot_usage(payload: BotUsageLogRequest, db: AsyncSession = Depends(get_db)):
    repo = AnalyticsRepository(db)
    await repo.log_bot_usage(
        command=payload.command,
        user_id=payload.user_id,
        username=payload.username,
        parameters=payload.parameters,
        response_time_ms=payload.response_time_ms,
    )
    return {"status": "logged"}


@router.get("/config/summary", response_model=AnalyticsConfigSummary)
async def get_config_summary(db: AsyncSession = Depends(get_db)):
    repo = AnalyticsRepository(db)
    return await repo.get_config_summary()
