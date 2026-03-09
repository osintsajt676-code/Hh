"""
Social Media OSINT - targeted social network checks.
Uses public endpoints, no credentials.
"""
import asyncio
import aiohttp
import re
import logging
from typing import Dict, List, Optional
from config import Config

logger = logging.getLogger(__name__)

class SocialOSINT:
    def __init__(self, config: Config):
        self.config = config
        self.proxy = config.PROXY_URL or None
        self.timeout = aiohttp.ClientTimeout(total=config.REQUEST_TIMEOUT)

    async def check_github(self, session: aiohttp.ClientSession, username: str) -> Dict:
        """GitHub public API - no key needed for basic info."""
        try:
            url = f"https://api.github.com/users/{username}"
            headers = {"Accept": "application/vnd.github.v3+json", "User-Agent": "OSINT-Bot"}
            async with session.get(url, headers=headers, proxy=self.proxy) as resp:
                if resp.status == 200:
                    d = await resp.json(content_type=None)
                    # Fetch repos
                    repos_url = f"https://api.github.com/users/{username}/repos?per_page=10&sort=updated"
                    repos = []
                    async with session.get(repos_url, headers=headers, proxy=self.proxy) as r2:
                        if r2.status == 200:
                            rdata = await r2.json(content_type=None)
                            repos = [
                                {"name": r.get("name"), "stars": r.get("stargazers_count", 0),
                                 "language": r.get("language"), "description": r.get("description", "")[:60]}
                                for r in rdata[:5]
                            ]
                    return {
                        "platform": "GitHub",
                        "found": True,
                        "url": d.get("html_url"),
                        "name": d.get("name", ""),
                        "bio": d.get("bio", ""),
                        "company": d.get("company", ""),
                        "location": d.get("location", ""),
                        "email": d.get("email", ""),
                        "blog": d.get("blog", ""),
                        "twitter": d.get("twitter_username", ""),
                        "public_repos": d.get("public_repos", 0),
                        "followers": d.get("followers", 0),
                        "following": d.get("following", 0),
                        "created_at": d.get("created_at", ""),
                        "updated_at": d.get("updated_at", ""),
                        "avatar": d.get("avatar_url", ""),
                        "hireable": d.get("hireable", False),
                        "top_repos": repos,
                    }
                elif resp.status == 404:
                    return {"platform": "GitHub", "found": False}
                return {"platform": "GitHub", "found": None, "error": f"HTTP {resp.status}"}
        except Exception as e:
            return {"platform": "GitHub", "found": None, "error": str(e)}

    async def check_reddit(self, session: aiohttp.ClientSession, username: str) -> Dict:
        """Reddit public API."""
        try:
            url = f"https://www.reddit.com/user/{username}/about.json"
            headers = {"User-Agent": "OSINT-Bot/1.0"}
            async with session.get(url, headers=headers, proxy=self.proxy) as resp:
                if resp.status == 200:
                    data = await resp.json(content_type=None)
                    d = data.get("data", {})
                    return {
                        "platform": "Reddit",
                        "found": True,
                        "url": f"https://reddit.com/u/{username}",
                        "karma_post": d.get("link_karma", 0),
                        "karma_comment": d.get("comment_karma", 0),
                        "total_karma": d.get("total_karma", 0),
                        "created_utc": d.get("created_utc", 0),
                        "is_mod": d.get("is_mod", False),
                        "is_gold": d.get("is_gold", False),
                        "verified": d.get("verified", False),
                        "icon_img": d.get("icon_img", ""),
                        "subreddits_mod": [],
                    }
                elif resp.status in [404, 302]:
                    return {"platform": "Reddit", "found": False}
                return {"platform": "Reddit", "found": None, "error": f"HTTP {resp.status}"}
        except Exception as e:
            return {"platform": "Reddit", "found": None, "error": str(e)}

    async def check_twitter(self, session: aiohttp.ClientSession, username: str) -> Dict:
        """Twitter/X profile check (public, no API key)."""
        try:
            url = f"https://x.com/{username}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml",
            }
            async with session.get(url, headers=headers, proxy=self.proxy, allow_redirects=True) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    # Check if profile exists (not suspended/not found)
                    if "This account doesn't exist" in text or "account has been suspended" in text:
                        return {"platform": "Twitter/X", "found": False, "note": "Suspended or deleted"}
                    # Try to extract basic info from meta tags
                    og_desc = re.search(r'<meta property="og:description" content="([^"]*)"', text)
                    og_title = re.search(r'<meta property="og:title" content="([^"]*)"', text)
                    return {
                        "platform": "Twitter/X",
                        "found": True,
                        "url": f"https://x.com/{username}",
                        "title": og_title.group(1) if og_title else "",
                        "description": og_desc.group(1) if og_desc else "",
                    }
                elif resp.status == 404:
                    return {"platform": "Twitter/X", "found": False}
                return {"platform": "Twitter/X", "found": None}
        except Exception as e:
            return {"platform": "Twitter/X", "found": None, "error": str(e)}

    async def check_instagram(self, session: aiohttp.ClientSession, username: str) -> Dict:
        """Instagram profile check (public endpoint)."""
        try:
            url = f"https://www.instagram.com/{username}/"
            headers = {
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)",
                "Accept": "text/html",
            }
            async with session.get(url, headers=headers, proxy=self.proxy) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    if "Sorry, this page isn't available" in text:
                        return {"platform": "Instagram", "found": False}
                    # Extract meta info
                    og_desc = re.search(r'<meta property="og:description" content="([^"]*)"', text)
                    og_title = re.search(r'<meta property="og:title" content="([^"]*)"', text)
                    og_img = re.search(r'<meta property="og:image" content="([^"]*)"', text)
                    return {
                        "platform": "Instagram",
                        "found": True,
                        "url": f"https://www.instagram.com/{username}/",
                        "title": og_title.group(1) if og_title else "",
                        "description": og_desc.group(1) if og_desc else "",
                        "image": og_img.group(1) if og_img else "",
                    }
                elif resp.status == 404:
                    return {"platform": "Instagram", "found": False}
                return {"platform": "Instagram", "found": None}
        except Exception as e:
            return {"platform": "Instagram", "found": None, "error": str(e)}

    async def check_tiktok(self, session: aiohttp.ClientSession, username: str) -> Dict:
        """TikTok profile check."""
        try:
            url = f"https://www.tiktok.com/@{username}"
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            async with session.get(url, headers=headers, proxy=self.proxy, allow_redirects=True) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    if "Couldn't find this account" in text or "このアカウントが見つかりませんでした" in text:
                        return {"platform": "TikTok", "found": False}
                    og_desc = re.search(r'<meta property="og:description" content="([^"]*)"', text)
                    og_title = re.search(r'<meta property="og:title" content="([^"]*)"', text)
                    return {
                        "platform": "TikTok",
                        "found": True,
                        "url": f"https://www.tiktok.com/@{username}",
                        "title": og_title.group(1) if og_title else "",
                        "description": og_desc.group(1) if og_desc else "",
                    }
                return {"platform": "TikTok", "found": None}
        except Exception as e:
            return {"platform": "TikTok", "found": None, "error": str(e)}

    async def check_telegram(self, session: aiohttp.ClientSession, username: str) -> Dict:
        """Telegram public profile check."""
        try:
            url = f"https://t.me/{username}"
            async with session.get(url, proxy=self.proxy) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    if "tgme_page_title" in text:
                        title_match = re.search(r'<div class="tgme_page_title"><span[^>]*>([^<]+)</span>', text)
                        desc_match = re.search(r'<div class="tgme_page_description">([^<]+)', text)
                        subscribers_match = re.search(r'(\d[\d\s]*)\s*(members|subscribers|followers)', text)
                        return {
                            "platform": "Telegram",
                            "found": True,
                            "url": f"https://t.me/{username}",
                            "title": title_match.group(1).strip() if title_match else "",
                            "description": desc_match.group(1).strip() if desc_match else "",
                            "subscribers": subscribers_match.group(0) if subscribers_match else "",
                        }
                    return {"platform": "Telegram", "found": False}
                return {"platform": "Telegram", "found": None}
        except Exception as e:
            return {"platform": "Telegram", "found": None, "error": str(e)}

    async def check_steam(self, session: aiohttp.ClientSession, username: str) -> Dict:
        """Steam community profile check."""
        try:
            url = f"https://steamcommunity.com/id/{username}"
            headers = {"User-Agent": "Mozilla/5.0"}
            async with session.get(url, headers=headers, proxy=self.proxy) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    if "The specified profile could not be found" in text or "error_ctn" in text:
                        return {"platform": "Steam", "found": False}
                    name_match = re.search(r'<span class="actual_persona_name">([^<]+)</span>', text)
                    return {
                        "platform": "Steam",
                        "found": True,
                        "url": f"https://steamcommunity.com/id/{username}",
                        "display_name": name_match.group(1) if name_match else "",
                    }
                return {"platform": "Steam", "found": None}
        except Exception as e:
            return {"platform": "Steam", "found": None, "error": str(e)}

    async def check_vk(self, session: aiohttp.ClientSession, username: str) -> Dict:
        """VKontakte profile check."""
        try:
            url = f"https://vk.com/{username}"
            headers = {"User-Agent": "Mozilla/5.0", "Accept-Language": "ru-RU,ru;q=0.9"}
            async with session.get(url, headers=headers, proxy=self.proxy) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    if "404" in text and "page not found" in text.lower():
                        return {"platform": "VK", "found": False}
                    og_title = re.search(r'<meta property="og:title" content="([^"]*)"', text)
                    og_desc = re.search(r'<meta property="og:description" content="([^"]*)"', text)
                    return {
                        "platform": "VK",
                        "found": True,
                        "url": f"https://vk.com/{username}",
                        "title": og_title.group(1) if og_title else "",
                        "description": og_desc.group(1) if og_desc else "",
                    }
                return {"platform": "VK", "found": None}
        except Exception as e:
            return {"platform": "VK", "found": None, "error": str(e)}

    async def check_youtube(self, session: aiohttp.ClientSession, username: str) -> Dict:
        """YouTube channel check."""
        try:
            url = f"https://www.youtube.com/@{username}"
            headers = {"User-Agent": "Mozilla/5.0"}
            async with session.get(url, headers=headers, proxy=self.proxy) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    og_title = re.search(r'<meta property="og:title" content="([^"]*)"', text)
                    og_desc = re.search(r'<meta name="description" content="([^"]*)"', text)
                    return {
                        "platform": "YouTube",
                        "found": True,
                        "url": f"https://www.youtube.com/@{username}",
                        "title": og_title.group(1) if og_title else "",
                        "description": og_desc.group(1) if og_desc else "",
                    }
                elif resp.status == 404:
                    return {"platform": "YouTube", "found": False}
                return {"platform": "YouTube", "found": None}
        except Exception as e:
            return {"platform": "YouTube", "found": None, "error": str(e)}

    async def scan(self, username: str) -> List[Dict]:
        """Run all social network checks."""
        connector = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(connector=connector, timeout=self.timeout) as session:
            tasks = [
                self.check_github(session, username),
                self.check_reddit(session, username),
                self.check_twitter(session, username),
                self.check_instagram(session, username),
                self.check_tiktok(session, username),
                self.check_telegram(session, username),
                self.check_steam(session, username),
                self.check_vk(session, username),
                self.check_youtube(session, username),
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        return [r for r in results if isinstance(r, dict)]
