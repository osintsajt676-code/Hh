"""
Username Scanner - real async HTTP checks against 500+ sites.
Uses WhatsMyName + Sherlock databases.
"""
import asyncio
import aiohttp
import logging
from typing import List, Dict, Optional, Callable
from modules.sites_db import get_sites_list

logger = logging.getLogger(__name__)

class UsernameScanner:
    def __init__(self, config, proxy: Optional[str] = None):
        self.config = config
        self.proxy = proxy or config.PROXY_URL or None
        self.timeout = aiohttp.ClientTimeout(total=config.REQUEST_TIMEOUT)
        self.semaphore = asyncio.Semaphore(config.MAX_CONCURRENT)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

    async def check_site(
        self,
        session: aiohttp.ClientSession,
        username: str,
        site: Dict,
    ) -> Optional[Dict]:
        url_template = site.get("uri_check", "")
        if not url_template or "{}" not in url_template:
            return None

        url = url_template.replace("{}", username)
        expected_code = site.get("e_code", 200)
        error_string = site.get("m_string", "") or site.get("e_string", "")

        async with self.semaphore:
            try:
                async with session.get(
                    url,
                    headers=self.headers,
                    proxy=self.proxy,
                    allow_redirects=True,
                    ssl=False,
                ) as resp:
                    status = resp.status

                    # Check by status code
                    if expected_code and status == expected_code:
                        # If error string defined, check it's NOT in response (means user found)
                        if error_string:
                            try:
                                text = await resp.text(errors="ignore")
                                if error_string in text:
                                    return None  # Error string present = not found
                            except Exception:
                                pass
                        return {
                            "name": site["name"],
                            "url": url,
                            "status": status,
                        }

            except asyncio.TimeoutError:
                pass
            except Exception as e:
                logger.debug(f"Error checking {site['name']}: {e}")
        return None

    async def scan(
        self,
        username: str,
        progress_callback: Optional[Callable] = None,
    ) -> List[Dict]:
        sites = await get_sites_list()
        total = len(sites)
        found = []
        checked = 0

        connector = aiohttp.TCPConnector(ssl=False, limit=100, ttl_dns_cache=300)

        async with aiohttp.ClientSession(
            connector=connector,
            timeout=self.timeout,
        ) as session:
            # Process in batches for progress updates
            batch_size = 50
            for i in range(0, total, batch_size):
                batch = sites[i:i + batch_size]
                tasks = [self.check_site(session, username, site) for site in batch]
                results = await asyncio.gather(*tasks, return_exceptions=True)

                for result in results:
                    if isinstance(result, dict) and result:
                        found.append(result)

                checked += len(batch)

                if progress_callback:
                    try:
                        await progress_callback(checked, total, len(found))
                    except Exception:
                        pass

        return found
