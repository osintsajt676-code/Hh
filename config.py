"""
Configuration - API keys and settings.
All public sources work WITHOUT keys.
Optional keys unlock premium sources.
"""
import os
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class Config:
    # === REQUIRED ===
    BOT_TOKEN: str = field(default_factory=lambda: os.getenv("BOT_TOKEN", ""))

    # === OPTIONAL API KEYS (leave empty for public-only mode) ===
    HIBP_API_KEY: str = field(default_factory=lambda: os.getenv("HIBP_API_KEY", ""))
    HUNTER_API_KEY: str = field(default_factory=lambda: os.getenv("HUNTER_API_KEY", ""))
    INTELX_API_KEY: str = field(default_factory=lambda: os.getenv("INTELX_API_KEY", ""))
    SHODAN_API_KEY: str = field(default_factory=lambda: os.getenv("SHODAN_API_KEY", ""))
    IPINFO_TOKEN: str = field(default_factory=lambda: os.getenv("IPINFO_TOKEN", ""))

    # === RATE LIMITING ===
    REQUEST_DELAY: float = 0.3       # seconds between requests
    MAX_CONCURRENT: int = 30         # concurrent async requests
    REQUEST_TIMEOUT: int = 10        # seconds per request

    # === PROXY (optional) ===
    # Format: "socks5://user:pass@host:port" or "http://host:port"
    PROXY_URL: str = field(default_factory=lambda: os.getenv("PROXY_URL", ""))

    # === LIMITS ===
    MAX_RESULTS_PER_USER: int = 500
    ALLOWED_USERS: list = field(default_factory=list)  # Empty = all users allowed

    # === HEADERS ===
    DEFAULT_HEADERS: dict = field(default_factory=lambda: {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    })
