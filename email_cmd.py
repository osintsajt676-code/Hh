"""
/email command - email OSINT.
"""
import re
import logging
from aiogram.types import Message
from config import Config
from modules.email_osint import EmailOSINT
from modules.formatter import format_email_results, chunk_message

logger = logging.getLogger(__name__)

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

async def cmd_email(msg: Message, config: Config):
    parts = msg.text.strip().split(maxsplit=1)
    if len(parts) < 2:
        await msg.answer("❌ Usage: /email <email>\n\nExample: /email user@example.com")
        return

    email = parts[1].strip().lower()
    if not EMAIL_REGEX.match(email):
        await msg.answer("❌ Invalid email format.")
        return

    progress_msg = await msg.answer(
        f"🔍 Running email OSINT on `{email}`...\n"
        f"⏳ Checking public databases...",
        parse_mode="Markdown"
    )

    try:
        osint = EmailOSINT(config)
        results = await osint.scan(email)

        result_text = format_email_results(email, results)
        chunks = chunk_message(result_text)

        await progress_msg.edit_text(chunks[0], parse_mode="Markdown", disable_web_page_preview=True)
        for chunk in chunks[1:]:
            await msg.answer(chunk, parse_mode="Markdown", disable_web_page_preview=True)

    except Exception as e:
        logger.error(f"Email scan error: {e}")
        await progress_msg.edit_text(f"❌ Error: {e}")
