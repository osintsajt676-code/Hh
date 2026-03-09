"""
HTTP Client - async requests with rate limiting, proxy support, retries.
"""
import asyncio
import aiohttp
import logging
from typing import Optional, Dict, Any
from config import Config

logger = logging.getLogger(__name__)

class HTTPClient:
    def __init__(self, config: Config):
        self.config = config
        self._semaphore = asyncio.Semaphore(config.MAX_CONCURRENT)
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        connector = aiohttp.TCPConnector(ssl=False, limit=100)
        timeout = aiohttp.ClientTimeout(total=self.config.REQUEST_TIMEOUT)
        self._session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=self.config.DEFAULT_HEADERS
        )
        return self

    async def __aexit__(self, *args):
        if self._session:
            await self._session.close()

    async def get(
        self,
        url: str,
        headers: Optional[Dict] = None,
        params: Optional[Dict] = None,
        allow_redirects: bool = True,
        return_json: bool = False,
        return_text: bool = False,
    ) -> Optional[Any]:
        proxy = self.config.PROXY_URL or None
        async with self._semaphore:
            try:
                await asyncio.sleep(self.config.REQUEST_DELAY)
                async with self._session.get(
                    url,
                    headers=headers,
                    params=params,
                    proxy=proxy,
                    allow_redirects=allow_redirects,
                    ssl=False,
                ) as resp:
                    if return_json:
                        return await resp.json(content_type=None)
                    if return_text:
                        return await resp.text()
                    return resp.status
            except asyncio.TimeoutError:
                logger.debug(f"Timeout: {url}")
                return None
            except Exception as e:
                logger.debug(f"Error {url}: {e}")
                return None

    async def post(
        self,
        url: str,
        data: Optional[Dict] = None,
        json: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        return_json: bool = False,
    ) -> Optional[Any]:
        proxy = self.config.PROXY_URL or None
        async with self._semaphore:
            try:
                await asyncio.sleep(self.config.REQUEST_DELAY)
                async with self._session.post(
                    url,
                    data=data,
                    json=json,
                    headers=headers,
                    proxy=proxy,
                    ssl=False,
                ) as resp:
                    if return_json:
                        return await resp.json(content_type=None)
                    return resp.status
            except Exception as e:
                logger.debug(f"POST error {url}: {e}")
                return None
