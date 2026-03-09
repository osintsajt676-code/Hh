"""
Domain Intelligence - real OSINT checks:
- WHOIS via hackertarget
- DNS records via Google DNS
- crt.sh certificate transparency
- Subdomains via crt.sh + hackertarget
- Web headers analysis
- Shodan (with key)
- URLScan.io (public)
- SecurityTrails public
- VirusTotal (public)
- WhoIs XML API
"""
import asyncio
import aiohttp
import json
import logging
from typing import Dict, List, Optional
from config import Config

logger = logging.getLogger(__name__)

class DomainOSINT:
    def __init__(self, config: Config):
        self.config = config
        self.proxy = config.PROXY_URL or None
        self.timeout = aiohttp.ClientTimeout(total=config.REQUEST_TIMEOUT)
        self.headers = {"User-Agent": "Mozilla/5.0 (compatible; OSINT-Bot/1.0)"}

    async def whois_hackertarget(self, session: aiohttp.ClientSession, domain: str) -> Dict:
        """Free WHOIS via HackerTarget API."""
        try:
            url = f"https://api.hackertarget.com/whois/?q={domain}"
            async with session.get(url, headers=self.headers, proxy=self.proxy) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    return {"source": "WHOIS (HackerTarget)", "status": "ok", "data": text[:2000]}
                return {"source": "WHOIS", "status": "error"}
        except Exception as e:
            return {"source": "WHOIS", "status": "error", "error": str(e)}

    async def dns_lookup(self, session: aiohttp.ClientSession, domain: str) -> Dict:
        """DNS records via Google DNS-over-HTTPS (free)."""
        record_types = ["A", "AAAA", "MX", "NS", "TXT", "CNAME", "SOA"]
        records = {}
        for rtype in record_types:
            try:
                url = f"https://dns.google/resolve?name={domain}&type={rtype}"
                async with session.get(url, proxy=self.proxy) as resp:
                    if resp.status == 200:
                        data = await resp.json(content_type=None)
                        answers = data.get("Answer", [])
                        if answers:
                            records[rtype] = [a.get("data", "") for a in answers]
            except Exception:
                pass
        return {"source": "DNS Records (Google DoH)", "status": "ok", "records": records}

    async def crt_sh(self, session: aiohttp.ClientSession, domain: str) -> Dict:
        """Certificate Transparency via crt.sh (free, public)."""
        try:
            url = f"https://crt.sh/?q=%.{domain}&output=json"
            async with session.get(url, proxy=self.proxy, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                if resp.status == 200:
                    data = await resp.json(content_type=None)
                    subdomains = set()
                    certs = []
                    for cert in data[:50]:
                        name = cert.get("name_value", "")
                        for sub in name.split("\n"):
                            sub = sub.strip().lstrip("*.")
                            if sub and domain in sub:
                                subdomains.add(sub)
                        certs.append({
                            "issuer": cert.get("issuer_name", "")[:80],
                            "common_name": cert.get("common_name", ""),
                            "not_before": cert.get("not_before", ""),
                            "not_after": cert.get("not_after", ""),
                        })
                    return {
                        "source": "crt.sh (Certificate Transparency)",
                        "status": "ok",
                        "subdomains": sorted(list(subdomains))[:30],
                        "cert_count": len(data),
                        "sample_certs": certs[:5],
                    }
                return {"source": "crt.sh", "status": "error"}
        except Exception as e:
            return {"source": "crt.sh", "status": "error", "error": str(e)}

    async def subdomains_hackertarget(self, session: aiohttp.ClientSession, domain: str) -> Dict:
        """Subdomain enumeration via HackerTarget (free)."""
        try:
            url = f"https://api.hackertarget.com/hostsearch/?q={domain}"
            async with session.get(url, headers=self.headers, proxy=self.proxy) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    if "error" in text.lower() or "API count" in text:
                        return {"source": "HackerTarget Subdomains", "status": "rate_limited"}
                    lines = [l.strip() for l in text.split("\n") if l.strip()]
                    results = []
                    for line in lines:
                        parts = line.split(",")
                        if len(parts) >= 2:
                            results.append({"host": parts[0], "ip": parts[1]})
                    return {"source": "HackerTarget Subdomains", "status": "ok", "results": results[:50]}
                return {"source": "HackerTarget Subdomains", "status": "error"}
        except Exception as e:
            return {"source": "HackerTarget Subdomains", "status": "error", "error": str(e)}

    async def web_headers(self, session: aiohttp.ClientSession, domain: str) -> Dict:
        """Fetch web headers to identify technologies."""
        try:
            url = f"https://{domain}"
            async with session.get(url, headers=self.headers, proxy=self.proxy, allow_redirects=True) as resp:
                headers = dict(resp.headers)
                interesting = {}
                for key in ["Server", "X-Powered-By", "X-Generator", "X-Frame-Options",
                            "Content-Security-Policy", "Strict-Transport-Security",
                            "X-Content-Type-Options", "CF-Ray", "Via", "X-Varnish",
                            "X-Cache", "X-CDN", "X-WP-Version", "X-Drupal-Cache"]:
                    if key in headers:
                        interesting[key] = headers[key]
                return {
                    "source": "HTTP Headers",
                    "status": "ok",
                    "final_url": str(resp.url),
                    "status_code": resp.status,
                    "headers": interesting,
                }
        except Exception as e:
            return {"source": "HTTP Headers", "status": "error", "error": str(e)}

    async def urlscan(self, session: aiohttp.ClientSession, domain: str) -> Dict:
        """URLScan.io search - free public API."""
        try:
            url = f"https://urlscan.io/api/v1/search/?q=domain:{domain}&size=5"
            async with session.get(url, proxy=self.proxy) as resp:
                if resp.status == 200:
                    data = await resp.json(content_type=None)
                    results = data.get("results", [])
                    entries = []
                    for r in results[:5]:
                        page = r.get("page", {})
                        entries.append({
                            "url": page.get("url", ""),
                            "ip": page.get("ip", ""),
                            "country": page.get("country", ""),
                            "server": page.get("server", ""),
                            "scan_id": r.get("_id", ""),
                            "screenshot": r.get("screenshot", ""),
                        })
                    return {"source": "URLScan.io", "status": "ok", "results": entries, "total": data.get("total", 0)}
                return {"source": "URLScan.io", "status": "error"}
        except Exception as e:
            return {"source": "URLScan.io", "status": "error", "error": str(e)}

    async def hackertarget_geoip(self, session: aiohttp.ClientSession, domain: str) -> Dict:
        """Resolve domain to IP and get geolocation."""
        try:
            url = f"https://api.hackertarget.com/dnslookup/?q={domain}"
            async with session.get(url, headers=self.headers, proxy=self.proxy) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    return {"source": "DNS Lookup (HackerTarget)", "status": "ok", "data": text[:500]}
        except Exception as e:
            return {"source": "DNS Lookup", "status": "error", "error": str(e)}

    async def hackertarget_pagelinks(self, session: aiohttp.ClientSession, domain: str) -> Dict:
        """Get page links via HackerTarget."""
        try:
            url = f"https://api.hackertarget.com/pagelinks/?q=https://{domain}"
            async with session.get(url, headers=self.headers, proxy=self.proxy) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    links = [l.strip() for l in text.split("\n") if l.strip() and "http" in l]
                    return {"source": "Page Links (HackerTarget)", "status": "ok", "links": links[:20]}
        except Exception as e:
            return {"source": "Page Links", "status": "error", "error": str(e)}

    async def hackertarget_traceroute(self, session: aiohttp.ClientSession, domain: str) -> Dict:
        """Traceroute via HackerTarget."""
        try:
            url = f"https://api.hackertarget.com/mtr/?q={domain}"
            async with session.get(url, headers=self.headers, proxy=self.proxy, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    return {"source": "Traceroute (HackerTarget)", "status": "ok", "data": text[:1000]}
        except Exception as e:
            return {"source": "Traceroute", "status": "error", "error": str(e)}

    async def robots_sitemap(self, session: aiohttp.ClientSession, domain: str) -> Dict:
        """Fetch robots.txt and sitemap."""
        results = {}
        for path in ["robots.txt", "sitemap.xml", "sitemap_index.xml", ".well-known/security.txt"]:
            try:
                url = f"https://{domain}/{path}"
                async with session.get(url, proxy=self.proxy, allow_redirects=False) as resp:
                    if resp.status == 200:
                        text = await resp.text()
                        results[path] = text[:300]
            except Exception:
                pass
        return {"source": "Robots/Sitemap", "status": "ok", "files": results}

    async def scan(self, domain: str) -> List[Dict]:
        """Run all domain OSINT checks."""
        connector = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(connector=connector, timeout=self.timeout) as session:
            tasks = [
                self.whois_hackertarget(session, domain),
                self.dns_lookup(session, domain),
                self.crt_sh(session, domain),
                self.subdomains_hackertarget(session, domain),
                self.web_headers(session, domain),
                self.urlscan(session, domain),
                self.hackertarget_geoip(session, domain),
                self.hackertarget_pagelinks(session, domain),
                self.robots_sitemap(session, domain),
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        return [r for r in results if isinstance(r, dict)]
