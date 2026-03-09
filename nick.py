"""
/nick command - username scan across 500+ websites.
"""
import asyncio
import logging
from aiogram.types import Message
from config import Config
from modules.username_scanner import UsernameScanner
from modules.formatter import format_nick_results, chunk_message

logger = logging.getLogger(__name__)

async def cmd_nick(msg: Message, config: Config):
    parts = msg.text.strip().split(maxsplit=1)
    if len(parts) < 2:
        await msg.answer("❌ Usage: /nick <username>\n\nExample: /nick johndoe")
        return

    username = parts[1].strip().lower()
    if len(username) < 2 or len(username) > 50:
        await msg.answer("❌ Username must be 2-50 characters.")
        return

    # Send initial progress message
    progress_msg = await msg.answer(
        f"🔍 Scanning `{username}` across public websites...\n"
        f"⏳ Loading sites database...",
        parse_mode="Markdown"
    )

    scanner = UsernameScanner(config)
    found = []
    total_sites = [0]

    async def update_progress(checked: int, total: int, found_count: int):
        total_sites[0] = total
        percent = int((checked / total) * 100) if total > 0 else 0
        bar = "█" * (percent // 10) + "░" * (10 - percent // 10)
        try:
            await progress_msg.edit_text(
                f"🔍 Scanning `{username}`...\n"
                f"[{bar}] {percent}%\n"
                f"Checked: {checked}/{total} sites\n"
                f"✅ Found: {found_count} accounts",
                parse_mode="Markdown"
            )
        except Exception:
            pass

    try:
        found = await scanner.scan(username, progress_callback=update_progress)
    except Exception as e:
        logger.error(f"Nick scan error: {e}")
        await progress_msg.edit_text(f"❌ Scan error: {e}")
        return

    # Format and send results
    result_text = format_nick_results(username, found, total_sites[0])
    chunks = chunk_message(result_text)

    try:
        await progress_msg.edit_text(chunks[0], parse_mode="Markdown", disable_web_page_preview=True)
    except Exception:
        await msg.answer(chunks[0], parse_mode="Markdown", disable_web_page_preview=True)

    for chunk in chunks[1:]:
        await msg.answer(chunk, parse_mode="Markdown", disable_web_page_preview=True)
