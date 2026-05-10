from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.schemas.openapi import (
    CrawlerSourceSummary, DataLayerSummary,
    BotUsageSummary, AnalyticsConfigSummary,
)


class AnalyticsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_crawler_source_summary(self) -> List[CrawlerSourceSummary]:
        query = text("""
            SELECT
                cs.id::text,
                cs.name,
                cs.source_type,
                cs.active,
                cs.last_crawl,
                COUNT(cl.id) AS total_crawls,
                COALESCE(SUM(cl.items_extracted), 0) AS total_items,
                COUNT(cl.id) FILTER (WHERE cl.status_code >= 400 OR cl.error_message IS NOT NULL) AS error_count,
                CASE
                    WHEN COUNT(cl.id) > 0 THEN
                        ROUND(100.0 * COUNT(cl.id) FILTER (WHERE cl.status_code < 400 AND cl.error_message IS NULL) / COUNT(cl.id), 1)
                    ELSE 100.0
                END AS success_rate
            FROM crawl_source cs
            LEFT JOIN crawl_log cl ON cl.source_id = cs.id
            GROUP BY cs.id, cs.name, cs.source_type, cs.active, cs.last_crawl
            ORDER BY cs.name
        """)
        result = await self.session.execute(query)
        rows = result.fetchall()
        return [
            CrawlerSourceSummary(
                id=r[0], name=r[1], source_type=r[2],
                active=r[3], last_crawl=r[4],
                total_crawls=r[5], total_items=r[6],
                error_count=r[7], success_rate=r[8],
            )
            for r in rows
        ]

    async def get_data_layer_summary(self) -> DataLayerSummary:
        query = text("""
            SELECT
                (SELECT COUNT(*) FROM trending_food) AS total_foods,
                (SELECT COUNT(*) FROM recipe) AS total_recipes,
                (SELECT COUNT(*) FROM stored_ingredient) AS total_ingredients,
                (SELECT COUNT(*) FROM crawl_log) AS total_logs
        """)
        result = await self.session.execute(query)
        totals = result.fetchone()

        cat_query = text("""
            SELECT category::text, COUNT(*) FROM trending_food GROUP BY category ORDER BY category
        """)
        cat_result = await self.session.execute(cat_query)
        foods_by_category = {row[0]: row[1] for row in cat_result.fetchall()}

        src_query = text("""
            SELECT source_type::text, COUNT(*) FROM recipe GROUP BY source_type ORDER BY source_type
        """)
        src_result = await self.session.execute(src_query)
        recipes_by_source = {row[0]: row[1] for row in src_result.fetchall()}

        reg_query = text("""
            SELECT region::text, COUNT(*) FROM trending_food GROUP BY region ORDER BY region
        """)
        reg_result = await self.session.execute(reg_query)
        recipes_by_region = {row[0]: row[1] for row in reg_result.fetchall()}

        return DataLayerSummary(
            total_trending_foods=totals[0],
            total_recipes=totals[1],
            total_ingredients=totals[2],
            total_crawl_logs=totals[3],
            foods_by_category=foods_by_category,
            recipes_by_source=recipes_by_source,
            recipes_by_region=recipes_by_region,
        )

    async def get_bot_usage_summary(self) -> BotUsageSummary:
        totals_query = text("""
            SELECT
                COUNT(*) AS total,
                COUNT(DISTINCT user_id) AS unique_users,
                COALESCE(SUM(response_time_ms), 0) AS total_time,
                CASE WHEN COUNT(*) > 0 THEN ROUND(AVG(response_time_ms) FILTER (WHERE response_time_ms IS NOT NULL), 1) ELSE 0 END AS avg_time
            FROM bot_usage_log
        """)
        result = await self.session.execute(totals_query)
        totals = result.fetchone()

        cmd_query = text("""
            SELECT command, COUNT(*) FROM bot_usage_log GROUP BY command ORDER BY COUNT(*) DESC
        """)
        cmd_result = await self.session.execute(cmd_query)
        commands_by_name = {row[0]: row[1] for row in cmd_result.fetchall()}

        day_query = text("""
            SELECT DATE(created_at)::text, COUNT(*) FROM bot_usage_log
            GROUP BY DATE(created_at) ORDER BY DATE(created_at) DESC LIMIT 30
        """)
        day_result = await self.session.execute(day_query)
        usage_by_day = {row[0]: row[1] for row in day_result.fetchall()}

        return BotUsageSummary(
            total_commands=totals[0],
            unique_users=totals[1],
            commands_by_name=commands_by_name,
            usage_by_day=usage_by_day,
            total_response_time_ms=totals[2],
            avg_response_time_ms=totals[3],
        )

    async def log_bot_usage(self, command: str, user_id: int, username: str = None, parameters: str = None, response_time_ms: int = None):
        query = text("""
            INSERT INTO bot_usage_log (command, user_id, username, parameters, response_time_ms)
            VALUES (:command, :user_id, :username, :parameters, :response_time_ms)
        """)
        await self.session.execute(query, {
            "command": command,
            "user_id": user_id,
            "username": username,
            "parameters": parameters,
            "response_time_ms": response_time_ms,
        })
        await self.session.commit()

    async def get_config_summary(self) -> AnalyticsConfigSummary:
        query = text("""
            SELECT frequency::text, active, categories::text, regions::text, last_sent
            FROM alert_config ORDER BY created_at DESC LIMIT 1
        """)
        result = await self.session.execute(query)
        config = result.fetchone()

        src_query = text("""
            SELECT
                COUNT(*) FILTER (WHERE active = TRUE) AS active_sources,
                COUNT(*) AS total_sources
            FROM crawl_source
        """)
        src_result = await self.session.execute(src_query)
        sources = src_result.fetchone()

        import json
        categories = json.loads(config[2]) if config and config[2] else []
        regions = json.loads(config[3]) if config and config[3] else []

        return AnalyticsConfigSummary(
            alert_frequency=config[0] if config else "daily",
            alert_active=config[1] if config else True,
            categories=categories,
            regions=regions,
            last_alert_sent=config[4] if config else None,
            active_sources=sources[0] if sources else 0,
            total_sources=sources[1] if sources else 0,
        )
