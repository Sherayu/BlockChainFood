from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.repositories.config_repo import AlertConfigRepository
from app.schemas.openapi import AlertConfigResponse, AlertConfigUpdate
from typing import List

router = APIRouter(prefix="/api/v1/config", tags=["Configuration"])


@router.get("/alerts", response_model=AlertConfigResponse)
async def get_alert_config(db: AsyncSession = Depends(get_db)):
    repo = AlertConfigRepository(db)
    config = await repo.get_active()
    if not config:
        config = await repo.create(
            frequency="daily",
            categories=["desserts", "main-course", "baking"],
            regions=["global"],
            active=True,
        )
    return config


@router.put("/alerts", response_model=AlertConfigResponse)
async def update_alert_config(
    config_update: AlertConfigUpdate,
    db: AsyncSession = Depends(get_db),
):
    repo = AlertConfigRepository(db)
    config = await repo.get_active()
    if not config:
        raise HTTPException(status_code=404, detail="No alert config found")

    update_data = config_update.model_dump(exclude_unset=True)
    updated = await repo.update(config.id, **update_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Update failed")
    return updated


@router.get("/alerts/all", response_model=List[AlertConfigResponse])
async def list_all_configs(db: AsyncSession = Depends(get_db)):
    repo = AlertConfigRepository(db)
    return await repo.list()
