# run.py
import asyncio
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

async def _run():
    from app.main import main
    await main()

if __name__ == "__main__":
    asyncio.run(_run())
