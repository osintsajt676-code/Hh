"""
/social command - deep social network OSINT.
"""
import logging
from aiogram.types import Message
from config import Config
from modules.social_osint import SocialOSINT
from modules.formatter import format_social_results, chunk_message

logger = logging.getLogger(__name__)

async def cmd_social(msg: Message, config: Config):
    parts = msg.text.strip().split(maxsplit=1)
    if len(parts) < 2:
        await msg.answer("❌ Usage: /social <username>\n\nExample: /social johndoe")
        return

    username = parts[1].strip()
    if len(username) < 2 or len(username) > 50:
        await msg.answer("❌ Username must be 2-50 characters.")
        return

    progress_msg = await msg.answer(
        f"🔍 Social OSINT on `{username}`...\n"
        f"⏳ Checking GitHub, Reddit, Twitter, Instagram, TikTok, Telegram, VK, Steam, YouTube...",
        parse_mode="Markdown"
    )

    try:
        osint = SocialOSINT(config)
        results = await osint.scan(username)

        result_text = format_social_results(username, results)
        chunks = chunk_message(result_text)

        await progress_msg.edit_text(chunks[0], parse_mode="Markdown", disable_web_page_preview=True)
        for chunk in chunks[1:]:
            await msg.answer(chunk, parse_mode="Markdown", disable_web_page_preview=True)

    except Exception as e:
        logger.error(f"Social scan error: {e}")
        await progress_msg.edit_text(f"❌ Error: {e}")
