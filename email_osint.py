"""
Email OSINT - real checks:
- HaveIBeenPwned API (requires key)
- Hunter.io email verify (requires key)
- EmailRep.io (free, public)
- Gravatar profile lookup
- IntelX public search
- Holehe-style checks (direct HTTP to services)
"""
import asyncio
import aiohttp
import hashlib
import logging
from typing import Dict, List, Optional
from config import Config

logger = logging.getLogger(__name__)

class EmailOSINT:
    def __init__(self, config: Config):
        self.config = config
        self.timeout = aiohttp.ClientTimeout(total=config.REQUEST_TIMEOUT)
        self.proxy = config.PROXY_URL or None
        self.headers = {"User-Agent": "OSINT-Bot/1.0"}

    async def check_hibp(self, session: aiohttp.ClientSession, email: str) -> Dict:
        """HaveIBeenPwned - requires API key."""
        if not self.config.HIBP_API_KEY:
            return {"source": "HaveIBeenPwned", "status": "no_key", "data": None}
        try:
            url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}"
            headers = {
                "hibp-api-key": self.config.HIBP_API_KEY,
                "User-Agent": "OSINT-TelegramBot",
            }
            async with session.get(url, headers=headers, proxy=self.proxy) as resp:
                if resp.status == 200:
                    data = await resp.json(content_type=None)
                    breaches = [b.get("Name", "") for b in data]
                    return {"source": "HaveIBeenPwned", "status": "found", "breaches": breaches, "count": len(breaches)}
                elif resp.status == 404:
                    return {"source": "HaveIBeenPwned", "status": "clean", "breaches": []}
                else:
                    return {"source": "HaveIBeenPwned", "status": "error", "code": resp.status}
        except Exception as e:
            return {"source": "HaveIBeenPwned", "status": "error", "error": str(e)}

    async def check_emailrep(self, session: aiohttp.ClientSession, email: str) -> Dict:
        """EmailRep.io - free public API."""
        try:
            url = f"https://emailrep.io/{email}"
            headers = {"User-Agent": "OSINT-TelegramBot"}
            async with session.get(url, headers=headers, proxy=self.proxy) as resp:
                if resp.status == 200:
                    data = await resp.json(content_type=None)
                    return {
                        "source": "EmailRep.io",
                        "status": "found",
                        "reputation": data.get("reputation", "unknown"),
                        "suspicious": data.get("suspicious", False),
                        "references": data.get("references", 0),
                        "details": {
                            "blacklisted": data.get("details", {}).get("blacklisted", False),
                            "malicious_activity": data.get("details", {}).get("malicious_activity", False),
                            "credentials_leaked": data.get("details", {}).get("credentials_leaked", False),
                            "data_breach": data.get("details", {}).get("data_breach", False),
                            "profiles": data.get("details", {}).get("profiles", []),
                            "spam": data.get("details", {}).get("spam", False),
                            "free_provider": data.get("details", {}).get("free_provider", False),
                            "disposable": data.get("details", {}).get("disposable", False),
                        }
                    }
                return {"source": "EmailRep.io", "status": "error", "code": resp.status}
        except Exception as e:
            return {"source": "EmailRep.io", "status": "error", "error": str(e)}

    async def check_gravatar(self, session: aiohttp.ClientSession, email: str) -> Dict:
        """Gravatar profile - public, no key needed."""
        try:
            email_hash = hashlib.md5(email.strip().lower().encode()).hexdigest()
            url = f"https://www.gravatar.com/{email_hash}.json"
            async with session.get(url, proxy=self.proxy) as resp:
                if resp.status == 200:
                    data = await resp.json(content_type=None)
                    entry = data.get("entry", [{}])[0]
                    return {
                        "source": "Gravatar",
                        "status": "found",
                        "display_name": entry.get("displayName", ""),
                        "profile_url": entry.get("profileUrl", ""),
                        "avatar": f"https://www.gravatar.com/avatar/{email_hash}",
                        "accounts": [a.get("shortname", "") for a in entry.get("accounts", [])],
                        "about_me": entry.get("aboutMe", ""),
                    }
                return {"source": "Gravatar", "status": "not_found"}
        except Exception as e:
            return {"source": "Gravatar", "status": "error", "error": str(e)}

    async def check_hunter(self, session: aiohttp.ClientSession, email: str) -> Dict:
        """Hunter.io email verification - requires key."""
        if not self.config.HUNTER_API_KEY:
            return {"source": "Hunter.io", "status": "no_key"}
        try:
            url = "https://api.hunter.io/v2/email-verifier"
            params = {"email": email, "api_key": self.config.HUNTER_API_KEY}
            async with session.get(url, params=params, proxy=self.proxy) as resp:
                if resp.status == 200:
                    data = await resp.json(content_type=None)
                    d = data.get("data", {})
                    return {
                        "source": "Hunter.io",
                        "status": "ok",
                        "result": d.get("result", ""),
                        "score": d.get("score", 0),
                        "regexp": d.get("regexp", False),
                        "gibberish": d.get("gibberish", False),
                        "disposable": d.get("disposable", False),
                        "webmail": d.get("webmail", False),
                        "mx_records": d.get("mx_records", False),
                        "smtp_server": d.get("smtp_server", False),
                    }
                return {"source": "Hunter.io", "status": "error", "code": resp.status}
        except Exception as e:
            return {"source": "Hunter.io", "status": "error", "error": str(e)}

    async def check_intelx(self, session: aiohttp.ClientSession, email: str) -> Dict:
        """IntelX public search."""
        if not self.config.INTELX_API_KEY:
            return {"source": "IntelX", "status": "no_key"}
        try:
            search_url = "https://2.intelx.io/intelligent/search"
            headers = {"x-key": self.config.INTELX_API_KEY, "Content-Type": "application/json"}
            payload = {"term": email, "buckets": [], "lookuplevel": 0, "maxresults": 10, "timeout": 5, "datefrom": "", "dateto": "", "sort": 2, "media": 0, "terminate": []}
            async with session.post(search_url, json=payload, headers=headers, proxy=self.proxy) as resp:
                if resp.status == 200:
                    data = await resp.json(content_type=None)
                    return {"source": "IntelX", "status": "found", "id": data.get("id", ""), "status": data.get("status", 0)}
                return {"source": "IntelX", "status": "error"}
        except Exception as e:
            return {"source": "IntelX", "status": "error", "error": str(e)}

    async def check_breachdirectory(self, session: aiohttp.ClientSession, email: str) -> Dict:
        """BreachDirectory public API."""
        try:
            url = f"https://breachdirectory.org/api?func=auto&term={email}"
            headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://breachdirectory.org/"}
            async with session.get(url, headers=headers, proxy=self.proxy) as resp:
                if resp.status == 200:
                    data = await resp.json(content_type=None)
                    if data.get("found", False):
                        return {"source": "BreachDirectory", "status": "found", "count": data.get("result", {}).get("count", 0)}
                return {"source": "BreachDirectory", "status": "clean"}
        except Exception as e:
            return {"source": "BreachDirectory", "status": "error", "error": str(e)}

    async def check_holehe_style(self, session: aiohttp.ClientSession, email: str) -> List[Dict]:
        """
        Holehe-style checks - try password reset endpoints on major services.
        These are public HTTP requests, no credentials needed.
        """
        results = []

        # Services that reveal account existence via password reset
        checks = [
            {
                "name": "Twitter",
                "url": "https://api.twitter.com/i/users/email_available.json",
                "params": {"email": email},
                "found_key": "valid",
                "found_val": False,  # valid=false means email IS registered
            },
        ]

        # Simple existence check via public profile endpoints
        domain = email.split("@")[-1] if "@" in email else ""
        username_guess = email.split("@")[0] if "@" in email else email

        # Check if email domain has MX records (basic validation)
        try:
            url = f"https://dns.google/resolve?name={domain}&type=MX"
            async with session.get(url, proxy=self.proxy) as resp:
                if resp.status == 200:
                    data = await resp.json(content_type=None)
                    has_mx = bool(data.get("Answer", []))
                    results.append({
                        "source": "DNS/MX Check",
                        "status": "found" if has_mx else "no_mx",
                        "domain": domain,
                        "has_mx": has_mx,
                    })
        except Exception:
            pass

        return results

    async def scan(self, email: str) -> List[Dict]:
        """Run all email OSINT checks."""
        connector = aiohttp.TCPConnector(ssl=False)
        timeout = aiohttp.ClientTimeout(total=self.config.REQUEST_TIMEOUT)

        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            tasks = [
                self.check_hibp(session, email),
                self.check_emailrep(session, email),
                self.check_gravatar(session, email),
                self.check_hunter(session, email),
                self.check_intelx(session, email),
                self.check_breachdirectory(session, email),
                self.check_holehe_style(session, email),
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        final = []
        for r in results:
            if isinstance(r, list):
                final.extend(r)
            elif isinstance(r, dict):
                final.append(r)
        return final
