import aiohttp
import logging

logger = logging.getLogger(__name__)
BASE_URL = "https://docs.google.com/spreadsheets/d/{id}/export?format=csv&gid={gid}"

async def fetch_csv_text(spreadsheet_id: str, gid: int) -> str:
    url = BASE_URL.format(id=spreadsheet_id, gid=gid)
    logger.info("Загружаем CSV: %s", url)
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                logger.error(f"Ошибка загрузки CSV: %s", resp.status)
                return ""
            return await resp.text()
