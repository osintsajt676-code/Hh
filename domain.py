"""
/domain command - domain OSINT.
"""
import re
import logging
from aiogram.types import Message
from config import Config
from modules.domain_osint import DomainOSINT
from modules.formatter import format_domain_results, chunk_message

logger = logging.getLogger(__name__)

DOMAIN_REGEX = re.compile(r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$')

async def cmd_domain(msg: Message, config: Config):
    parts = msg.text.strip().split(maxsplit=1)
    if len(parts) < 2:
        await msg.answer("❌ Usage: /domain <domain>\n\nExample: /domain example.com")
        return

    domain = parts[1].strip().lower()
    domain = domain.replace("https://", "").replace("http://", "").split("/")[0]

    if not DOMAIN_REGEX.match(domain):
        await msg.answer("❌ Invalid domain format.\n\nExample: example.com")
        return

    progress_msg = await msg.answer(
        f"🔍 Domain intelligence on `{domain}`...\n"
        f"⏳ Running WHOIS, DNS, crt.sh, subdomain scan...",
        parse_mode="Markdown"
    )

    try:
        osint = DomainOSINT(config)
        results = await osint.scan(domain)

        result_text = format_domain_results(domain, results)
        chunks = chunk_message(result_text)

        await progress_msg.edit_text(chunks[0], parse_mode="Markdown", disable_web_page_preview=True)
        for chunk in chunks[1:]:
            await msg.answer(chunk, parse_mode="Markdown", disable_web_page_preview=True)

    except Exception as e:
        logger.error(f"Domain scan error: {e}")
        await progress_msg.edit_text(f"❌ Error: {e}")
