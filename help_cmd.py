from aiogram.types import Message

HELP_TEXT = """
🕵 *OSINT Telegram Bot*

*Commands:*

`/nick <username>` — Username search across 500\\+ websites
`/email <email>` — Email OSINT \\(breaches, reputation, profiles\\)
`/domain <domain>` — Domain intelligence \\(WHOIS, DNS, certs, subdomains\\)
`/ip <ip>` — IP geolocation, ASN, threat intel
`/social <username>` — Deep social network analysis

*Sources used:*
• WhatsMyName \\(500\\+ sites\\)
• Sherlock project database
• HaveIBeenPwned \\(with API key\\)
• EmailRep\\.io \\(free\\)
• Gravatar \\(free\\)
• Hunter\\.io \\(with API key\\)
• crt\\.sh certificate transparency
• HackerTarget APIs \\(free\\)
• ipinfo\\.io \\(free/with key\\)
• ip\\-api\\.com \\(free\\)
• BGPView\\.io \\(free\\)
• AlienVault OTX \\(free\\)
• URLScan\\.io \\(free\\)
• Google DNS\\-over\\-HTTPS \\(free\\)
• Shodan \\(with API key\\)
• GitHub public API
• Reddit public API
• Telegram public profiles
• VK public profiles
• Steam public API

*Legal note:* This bot uses only public OSINT sources\\. 
No private data, no hacking, no illegal activity\\.

`/help` — Show this message
"""

async def cmd_start(msg: Message):
    await msg.answer(
        "🕵 *OSINT Bot* — ready\\!\n\nType /help for commands\\.",
        parse_mode="MarkdownV2"
    )

async def cmd_help(msg: Message):
    await msg.answer(HELP_TEXT, parse_mode="MarkdownV2", disable_web_page_preview=True)
