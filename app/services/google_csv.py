import logging
from typing import Optional, List

import aiohttp

logger = logging.getLogger(__name__)

BASE_URL = "https://docs.google.com/spreadsheets/d/{id}/export?format=csv&gid={gid}"


async def fetch_csv_text(spreadsheet_id: str, gid: int) -> Optional[str]:
    url = BASE_URL.format(id=spreadsheet_id, gid=gid)
    logger.info("Загрузка CSV: GID=%s", gid)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    return await resp.text()

                logger.error("Ошибка загрузки CSV: GID=%s, статус=%s", gid, resp.status)
                return None

    except Exception as e:
        logger.error("Ошибка при загрузке GID=%s: %s", gid, e)
        return None


async def find_group_schedule(spreadsheet_id: str, gids: List[int], group_code: str) -> Optional[str]:
    logger.info("Поиск группы %s в листах: %s", group_code, gids)

    for gid in gids:
        csv_text = await fetch_csv_text(spreadsheet_id, gid)
        if csv_text and group_code in csv_text:
            logger.info("Группа %s найдена в GID=%s", group_code, gid)
            return csv_text

        if csv_text:
            logger.debug("Группа %s не найдена в GID=%s", group_code, gid)

    logger.warning("Группа %s не найдена ни в одном листе", group_code)
    return None
