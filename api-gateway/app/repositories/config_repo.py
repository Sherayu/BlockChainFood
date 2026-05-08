from app.repositories.base import BaseRepository
from app.models.alert_config import AlertConfig
from sqlalchemy import select
from typing import Optional


class AlertConfigRepository(BaseRepository[AlertConfig]):
    def __init__(self, session):
        super().__init__(AlertConfig, session)

    async def get_active(self) -> Optional[AlertConfig]:
        result = await self.session.execute(
            select(AlertConfig).where(AlertConfig.active == True).limit(1)
        )
        return result.scalar_one_or_none()
