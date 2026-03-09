"""
/ip command - IP OSINT.
"""
import re
import logging
from aiogram.types import Message
from config import Config
from modules.ip_osint import IPOSINT
from modules.formatter import format_ip_results, chunk_message

logger = logging.getLogger(__name__)

IP_REGEX = re.compile(
    r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
)

async def cmd_ip(msg: Message, config: Config):
    parts = msg.text.strip().split(maxsplit=1)
    if len(parts) < 2:
        await msg.answer("❌ Usage: /ip <ip_address>\n\nExample: /ip 8.8.8.8")
        return

    ip = parts[1].strip()
    if not IP_REGEX.match(ip):
        await msg.answer("❌ Invalid IPv4 address.\n\nExample: /ip 8.8.8.8")
        return

    # Block private/loopback ranges
    private_ranges = ["10.", "192.168.", "127.", "172.16.", "172.17.", "0."]
    if any(ip.startswith(r) for r in private_ranges):
        await msg.answer("⚠️ Private/loopback IP addresses have no public OSINT data.")
        return

    progress_msg = await msg.answer(
        f"🔍 IP Intelligence on `{ip}`...\n"
        f"⏳ Checking geolocation, ASN, threats...",
        parse_mode="Markdown"
    )

    try:
        osint = IPOSINT(config)
        results = await osint.scan(ip)

        result_text = format_ip_results(ip, results)
        chunks = chunk_message(result_text)

        await progress_msg.edit_text(chunks[0], parse_mode="Markdown", disable_web_page_preview=True)
        for chunk in chunks[1:]:
            await msg.answer(chunk, parse_mode="Markdown", disable_web_page_preview=True)

    except Exception as e:
        logger.error(f"IP scan error: {e}")
        await progress_msg.edit_text(f"❌ Error: {e}")
