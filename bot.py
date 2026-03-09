import subprocess, sys
subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "aiogram==3.13.1", "aiohttp", "python-dotenv"])

from pathlib import Path
Path("logs").mkdir(exist_ok=True)
Path("data").mkdir(exist_ok=True)

import asyncio, logging, os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

from handlers import register_handlers
from config import Config

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", handlers=[logging.StreamHandler(sys.stdout)])
logger = logging.getLogger(__name__)

async def main():
    config = Config()
    if not config.BOT_TOKEN:
        logger.error("BOT_TOKEN not set! Add it in Secrets (Replit) or .env file")
        sys.exit(1)
    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    register_handlers(dp, config)
    logger.info("OSINT Bot started!")
    await dp.start_polling(bot, skip_updates=True)

if __name__ == "__main__":
    asyncio.run(main())
  
