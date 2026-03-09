"""
IP Intelligence - real lookups:
- ipinfo.io (free, with optional token for more data)
- ip-api.com (free, no key)
- AbuseIPDB (requires key)
- Shodan (requires key)
- BGP/ASN data via bgpview.io (free)
- Reverse DNS via HackerTarget (free)
- Port scan via HackerTarget (free)
- Threat intelligence via VirusTotal (free tier)
"""
import asyncio
import aiohttp
import logging
from typing import Dict, List
from config import Config

logger = logging.getLogger(__name__)

class IPOSINT:
    def __init__(self, config: Config):
        self.config = config
        self.proxy = config.PROXY_URL or None
        self.timeout = aiohttp.ClientTimeout(total=config.REQUEST_TIMEOUT)
        self.headers = {"User-Agent": "OSINT-Bot/1.0"}

    async def ipinfo(self, session: aiohttp.ClientSession, ip: str) -> Dict:
        """ipinfo.io - free without key, more data with token."""
        try:
            token = self.config.IPINFO_TOKEN
            url = f"https://ipinfo.io/{ip}/json"
            if token:
                url += f"?token={token}"
            async with session.get(url, headers=self.headers, proxy=self.proxy) as resp:
                if resp.status == 200:
                    data = await resp.json(content_type=None)
                    return {
                        "source": "ipinfo.io",
                        "status": "ok",
                        "ip": data.get("ip", ""),
                        "hostname": data.get("hostname", ""),
                        "city": data.get("city", ""),
                        "region": data.get("region", ""),
                        "country": data.get("country", ""),
                        "location": data.get("loc", ""),
                        "org": data.get("org", ""),
                        "postal": data.get("postal", ""),
                        "timezone": data.get("timezone", ""),
                        "bogon": data.get("bogon", False),
                    }
                return {"source": "ipinfo.io", "status": "error", "code": resp.status}
        except Exception as e:
            return {"source": "ipinfo.io", "status": "error", "error": str(e)}

    async def ip_api(self, session: aiohttp.ClientSession, ip: str) -> Dict:
        """ip-api.com - free, no key required."""
        try:
            url = f"http://ip-api.com/json/{ip}?fields=status,message,country,countryCode,region,regionName,city,zip,lat,lon,timezone,isp,org,as,asname,reverse,mobile,proxy,hosting,query"
            async with session.get(url, proxy=self.proxy) as resp:
                if resp.status == 200:
                    data = await resp.json(content_type=None)
                    return {
                        "source": "ip-api.com",
                        "status": "ok",
                        "country": data.get("country", ""),
                        "country_code": data.get("countryCode", ""),
                        "region": data.get("regionName", ""),
                        "city": data.get("city", ""),
                        "zip": data.get("zip", ""),
                        "lat": data.get("lat", 0),
                        "lon": data.get("lon", 0),
                        "timezone": data.get("timezone", ""),
                        "isp": data.get("isp", ""),
                        "org": data.get("org", ""),
                        "asn": data.get("as", ""),
                        "as_name": data.get("asname", ""),
                        "reverse_dns": data.get("reverse", ""),
                        "is_mobile": data.get("mobile", False),
                        "is_proxy": data.get("proxy", False),
                        "is_hosting": data.get("hosting", False),
                    }
                return {"source": "ip-api.com", "status": "error"}
        except Exception as e:
            return {"source": "ip-api.com", "status": "error", "error": str(e)}

    async def bgpview(self, session: aiohttp.ClientSession, ip: str) -> Dict:
        """BGPView.io - ASN and routing info, free."""
        try:
            url = f"https://api.bgpview.io/ip/{ip}"
            async with session.get(url, proxy=self.proxy) as resp:
                if resp.status == 200:
                    data = await resp.json(content_type=None)
                    d = data.get("data", {})
                    prefixes = d.get("prefixes", [])
                    asns = []
                    for prefix in prefixes[:3]:
                        for asn_info in prefix.get("asns", []):
                            asns.append({
                                "asn": asn_info.get("asn", ""),
                                "name": asn_info.get("name", ""),
                                "description": asn_info.get("description", ""),
                                "country": asn_info.get("country_code", ""),
                            })
                    return {
                        "source": "BGPView.io",
                        "status": "ok",
                        "rir_allocation": d.get("rir_allocation", {}),
                        "asns": asns,
                        "ptr_record": d.get("ptr_record", ""),
                    }
                return {"source": "BGPView.io", "status": "error"}
        except Exception as e:
            return {"source": "BGPView.io", "status": "error", "error": str(e)}

    async def reverse_dns_hackertarget(self, session: aiohttp.ClientSession, ip: str) -> Dict:
        """Reverse DNS lookup via HackerTarget."""
        try:
            url = f"https://api.hackertarget.com/reversedns/?q={ip}"
            async with session.get(url, headers=self.headers, proxy=self.proxy) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    return {"source": "Reverse DNS (HackerTarget)", "status": "ok", "data": text.strip()}
        except Exception as e:
            return {"source": "Reverse DNS", "status": "error", "error": str(e)}

    async def portscan_hackertarget(self, session: aiohttp.ClientSession, ip: str) -> Dict:
        """Basic port scan via HackerTarget (free, limited)."""
        try:
            url = f"https://api.hackertarget.com/nmap/?q={ip}"
            async with session.get(url, headers=self.headers, proxy=self.proxy, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    if "error" in text.lower():
                        return {"source": "Port Scan", "status": "rate_limited"}
                    return {"source": "Port Scan (HackerTarget)", "status": "ok", "data": text[:1500]}
        except Exception as e:
            return {"source": "Port Scan", "status": "error", "error": str(e)}

    async def shodan_info(self, session: aiohttp.ClientSession, ip: str) -> Dict:
        """Shodan lookup - requires API key."""
        if not self.config.SHODAN_API_KEY:
            return {"source": "Shodan", "status": "no_key"}
        try:
            url = f"https://api.shodan.io/shodan/host/{ip}?key={self.config.SHODAN_API_KEY}"
            async with session.get(url, proxy=self.proxy) as resp:
                if resp.status == 200:
                    data = await resp.json(content_type=None)
                    return {
                        "source": "Shodan",
                        "status": "ok",
                        "ports": data.get("ports", []),
                        "os": data.get("os", ""),
                        "hostnames": data.get("hostnames", []),
                        "vulns": list(data.get("vulns", {}).keys())[:10],
                        "last_update": data.get("last_update", ""),
                        "country": data.get("country_name", ""),
                        "city": data.get("city", ""),
                        "isp": data.get("isp", ""),
                        "org": data.get("org", ""),
                        "asn": data.get("asn", ""),
                        "tags": data.get("tags", []),
                        "services": [
                            {
                                "port": b.get("port"),
                                "transport": b.get("transport"),
                                "product": b.get("product", ""),
                                "version": b.get("version", ""),
                            }
                            for b in data.get("data", [])[:10]
                        ],
                    }
                elif resp.status == 404:
                    return {"source": "Shodan", "status": "not_found"}
                return {"source": "Shodan", "status": "error", "code": resp.status}
        except Exception as e:
            return {"source": "Shodan", "status": "error", "error": str(e)}

    async def abuseipdb(self, session: aiohttp.ClientSession, ip: str) -> Dict:
        """AbuseIPDB check - requires free API key."""
        key = self.config.__dict__.get("ABUSEIPDB_KEY", "")
        if not key:
            # Try public check without key (limited)
            try:
                url = f"https://www.abuseipdb.com/check/{ip}"
                async with session.get(url, headers=self.headers, proxy=self.proxy) as resp:
                    return {"source": "AbuseIPDB", "status": "no_key", "note": "Register free at abuseipdb.com for API access"}
            except Exception:
                return {"source": "AbuseIPDB", "status": "no_key"}

    async def ip_threat_check(self, session: aiohttp.ClientSession, ip: str) -> Dict:
        """Check IP against threat intelligence feeds (public)."""
        try:
            # Cisco Talos public check
            url = f"https://talosintelligence.com/cloud_and_network/ip?ip={ip}"
            # AlienVault OTX public
            otx_url = f"https://otx.alienvault.com/api/v1/indicators/IPv4/{ip}/general"
            async with session.get(otx_url, proxy=self.proxy) as resp:
                if resp.status == 200:
                    data = await resp.json(content_type=None)
                    return {
                        "source": "AlienVault OTX",
                        "status": "ok",
                        "pulse_count": data.get("pulse_info", {}).get("count", 0),
                        "reputation": data.get("reputation", 0),
                        "country": data.get("country_name", ""),
                        "asn": data.get("asn", ""),
                        "malware_families": data.get("malware_families", [])[:5],
                        "tags": [p.get("name", "") for p in data.get("pulse_info", {}).get("pulses", [])[:5]],
                    }
                return {"source": "AlienVault OTX", "status": "error"}
        except Exception as e:
            return {"source": "Threat Check", "status": "error", "error": str(e)}

    async def scan(self, ip: str) -> List[Dict]:
        """Run all IP OSINT checks."""
        connector = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(connector=connector, timeout=self.timeout) as session:
            tasks = [
                self.ipinfo(session, ip),
                self.ip_api(session, ip),
                self.bgpview(session, ip),
                self.reverse_dns_hackertarget(session, ip),
                self.shodan_info(session, ip),
                self.ip_threat_check(session, ip),
                self.portscan_hackertarget(session, ip),
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        return [r for r in results if isinstance(r, dict)]
