"""
Formatter - clean structured OSINT results for Telegram.
Handles Telegram 4096 char message limit.
"""
from typing import List, Dict, Any
import re

def escape_md(text: str) -> str:
    """Escape MarkdownV2 special chars."""
    if not text:
        return ""
    chars = r'\_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(chars)}])', r'\\\1', str(text))

def chunk_message(text: str, max_len: int = 4000) -> List[str]:
    """Split long messages into chunks."""
    if len(text) <= max_len:
        return [text]
    chunks = []
    while text:
        chunk = text[:max_len]
        # Try to split at newline
        last_nl = chunk.rfind("\n")
        if last_nl > max_len // 2:
            chunk = chunk[:last_nl]
        chunks.append(chunk)
        text = text[len(chunk):]
    return chunks

def format_nick_results(username: str, found: List[Dict], total_checked: int) -> str:
    total_found = len(found)
    lines = [
        f"🕵 *OSINT — Username Scan*",
        f"",
        f"🎯 Target: `{username}`",
        f"📊 Checked: {total_checked} sites",
        f"✅ Found: {total_found} accounts",
        f"",
    ]
    if not found:
        lines.append("❌ No public accounts found.")
    else:
        lines.append("*Found accounts:*")
        for item in found:
            name = item.get("name", "")
            url = item.get("url", "")
            lines.append(f"• [{name}]({url})")
    return "\n".join(lines)

def format_email_results(email: str, results: List[Dict]) -> str:
    lines = [
        f"🕵 *OSINT — Email Intelligence*",
        f"",
        f"📧 Target: `{email}`",
        f"",
    ]
    for r in results:
        source = r.get("source", "Unknown")
        status = r.get("status", "")

        if status == "no_key":
            lines.append(f"🔑 *{source}*: API key required")
            continue
        if status == "error":
            lines.append(f"⚠️ *{source}*: {r.get('error', 'Error')[:50]}")
            continue

        if source == "HaveIBeenPwned":
            if status == "found":
                breaches = r.get("breaches", [])
                lines.append(f"🔴 *HaveIBeenPwned*: FOUND in {r.get('count', 0)} breaches")
                for b in breaches[:8]:
                    lines.append(f"  ⚠️ {b}")
            elif status == "clean":
                lines.append(f"🟢 *HaveIBeenPwned*: No breaches found")

        elif source == "EmailRep.io":
            rep = r.get("reputation", "unknown")
            susp = "⚠️ SUSPICIOUS" if r.get("suspicious") else "✅ OK"
            lines.append(f"")
            lines.append(f"📋 *EmailRep.io*: {susp}")
            lines.append(f"  Reputation: {rep}")
            lines.append(f"  References: {r.get('references', 0)}")
            details = r.get("details", {})
            if details.get("credentials_leaked"):
                lines.append(f"  🔴 Credentials leaked: YES")
            if details.get("data_breach"):
                lines.append(f"  🔴 Data breach: YES")
            if details.get("blacklisted"):
                lines.append(f"  🔴 Blacklisted: YES")
            if details.get("disposable"):
                lines.append(f"  ⚠️ Disposable email: YES")
            if details.get("spam"):
                lines.append(f"  ⚠️ Spam reports: YES")
            profiles = details.get("profiles", [])
            if profiles:
                lines.append(f"  🌐 Profiles: {', '.join(profiles[:5])}")

        elif source == "Gravatar":
            if status == "found":
                lines.append(f"")
                lines.append(f"🟢 *Gravatar*: Profile found")
                if r.get("display_name"):
                    lines.append(f"  Name: {r['display_name']}")
                if r.get("profile_url"):
                    lines.append(f"  URL: {r['profile_url']}")
                if r.get("accounts"):
                    lines.append(f"  Accounts: {', '.join(r['accounts'][:5])}")
                if r.get("about_me"):
                    lines.append(f"  Bio: {r['about_me'][:100]}")
            else:
                lines.append(f"⚪ *Gravatar*: No profile")

        elif source == "Hunter.io":
            lines.append(f"")
            lines.append(f"🔍 *Hunter.io*:")
            lines.append(f"  Result: {r.get('result', '')}")
            lines.append(f"  Score: {r.get('score', 0)}/100")
            if r.get("disposable"): lines.append(f"  ⚠️ Disposable")
            if r.get("webmail"): lines.append(f"  ℹ️ Webmail")

        elif source == "BreachDirectory":
            if status == "found":
                lines.append(f"🔴 *BreachDirectory*: Found {r.get('count', '?')} records")
            else:
                lines.append(f"🟢 *BreachDirectory*: Clean")

        elif source == "DNS/MX Check":
            mx = "✅ Valid MX" if r.get("has_mx") else "❌ No MX records"
            lines.append(f"")
            lines.append(f"🌐 *DNS Check*: {mx} ({r.get('domain', '')})")

    return "\n".join(lines)

def format_domain_results(domain: str, results: List[Dict]) -> str:
    lines = [
        f"🕵 *OSINT — Domain Intelligence*",
        f"",
        f"🌐 Target: `{domain}`",
        f"",
    ]
    for r in results:
        source = r.get("source", "")
        status = r.get("status", "")

        if status in ["error", "rate_limited"]:
            lines.append(f"⚠️ *{source}*: {'Rate limited' if status == 'rate_limited' else r.get('error', 'Error')[:50]}")
            continue

        if "WHOIS" in source:
            data = r.get("data", "")
            lines.append(f"")
            lines.append(f"📋 *WHOIS Data:*")
            # Extract key fields
            for line in data.split("\n"):
                for key in ["Registrar:", "Creation Date:", "Expiry Date:", "Updated Date:", "Registrant", "Name Server:"]:
                    if key.lower() in line.lower() and ":" in line:
                        lines.append(f"  {line.strip()[:100]}")
                        break

        elif source == "DNS Records (Google DoH)":
            records = r.get("records", {})
            if records:
                lines.append(f"")
                lines.append(f"🔢 *DNS Records:*")
                for rtype, values in records.items():
                    for v in values[:3]:
                        lines.append(f"  {rtype}: {v[:80]}")

        elif "crt.sh" in source:
            subdomains = r.get("subdomains", [])
            lines.append(f"")
            lines.append(f"📜 *Certificate Transparency (crt.sh):*")
            lines.append(f"  Total certs: {r.get('cert_count', 0)}")
            lines.append(f"  Subdomains found: {len(subdomains)}")
            for sub in subdomains[:15]:
                lines.append(f"  • {sub}")

        elif "Subdomains" in source:
            results_list = r.get("results", [])
            if results_list:
                lines.append(f"")
                lines.append(f"🔎 *Subdomains (HackerTarget):*")
                for item in results_list[:15]:
                    lines.append(f"  • {item.get('host', '')} → {item.get('ip', '')}")

        elif source == "HTTP Headers":
            headers = r.get("headers", {})
            lines.append(f"")
            lines.append(f"🌍 *HTTP Headers:*")
            lines.append(f"  Status: {r.get('status_code', '')}")
            lines.append(f"  Final URL: {r.get('final_url', '')[:80]}")
            for k, v in headers.items():
                lines.append(f"  {k}: {v[:80]}")

        elif source == "URLScan.io":
            entries = r.get("results", [])
            lines.append(f"")
            lines.append(f"🔍 *URLScan.io:* {r.get('total', 0)} historical scans")
            for e in entries[:3]:
                lines.append(f"  • IP: {e.get('ip', '')} | Country: {e.get('country', '')}")
                lines.append(f"    Server: {e.get('server', '')} | [View scan](https://urlscan.io/result/{e.get('scan_id', '')}/)")

        elif "Robots" in source:
            files = r.get("files", {})
            for fname, content in files.items():
                lines.append(f"")
                lines.append(f"📄 *{fname}:*")
                lines.append(f"```\n{content[:300]}\n```")

    return "\n".join(lines)

def format_ip_results(ip: str, results: List[Dict]) -> str:
    lines = [
        f"🕵 *OSINT — IP Intelligence*",
        f"",
        f"🖥 Target: `{ip}`",
        f"",
    ]
    for r in results:
        source = r.get("source", "")
        status = r.get("status", "")

        if status == "no_key":
            lines.append(f"🔑 *{source}*: API key required")
            continue
        if status in ["error"]:
            lines.append(f"⚠️ *{source}*: {r.get('error', 'Error')[:60]}")
            continue

        if source == "ipinfo.io":
            lines.append(f"📍 *ipinfo.io:*")
            lines.append(f"  Location: {r.get('city', '')}, {r.get('region', '')}, {r.get('country', '')}")
            lines.append(f"  Coords: {r.get('location', '')}")
            lines.append(f"  Org: {r.get('org', '')}")
            lines.append(f"  Hostname: {r.get('hostname', '')}")
            lines.append(f"  Timezone: {r.get('timezone', '')}")
            if r.get("bogon"):
                lines.append(f"  ⚠️ Bogon/Private IP")

        elif source == "ip-api.com":
            proxy_str = "🔴 PROXY/VPN" if r.get("is_proxy") else "✅ Clean"
            hosting_str = "☁️ Hosting/DC" if r.get("is_hosting") else ""
            lines.append(f"")
            lines.append(f"🗺 *ip-api.com:*")
            lines.append(f"  ISP: {r.get('isp', '')}")
            lines.append(f"  ASN: {r.get('asn', '')} ({r.get('as_name', '')})")
            lines.append(f"  Proxy/VPN: {proxy_str} {hosting_str}")
            lines.append(f"  rDNS: {r.get('reverse_dns', '')}")

        elif source == "BGPView.io":
            lines.append(f"")
            lines.append(f"🔗 *BGP/Routing:*")
            for asn in r.get("asns", [])[:3]:
                lines.append(f"  AS{asn.get('asn', '')}: {asn.get('name', '')} ({asn.get('country', '')})")
                lines.append(f"  Description: {asn.get('description', '')[:80]}")
            if r.get("ptr_record"):
                lines.append(f"  PTR: {r['ptr_record']}")

        elif "Reverse DNS" in source:
            lines.append(f"")
            lines.append(f"🔄 *Reverse DNS:* {r.get('data', 'N/A')}")

        elif source == "Shodan":
            if status == "not_found":
                lines.append(f"")
                lines.append(f"🔍 *Shodan:* Not indexed")
            elif status == "ok":
                ports = r.get("ports", [])
                vulns = r.get("vulns", [])
                lines.append(f"")
                lines.append(f"🔍 *Shodan:*")
                lines.append(f"  OS: {r.get('os', 'Unknown')}")
                lines.append(f"  Ports: {', '.join(str(p) for p in ports[:15])}")
                if vulns:
                    lines.append(f"  🔴 Vulns: {', '.join(vulns[:5])}")
                for svc in r.get("services", [])[:5]:
                    lines.append(f"  Port {svc.get('port')}/{svc.get('transport', '')}: {svc.get('product', '')} {svc.get('version', '')}")

        elif source == "AlienVault OTX":
            pulse_count = r.get("pulse_count", 0)
            if pulse_count > 0:
                lines.append(f"")
                lines.append(f"🔴 *AlienVault OTX:* {pulse_count} threat pulses")
                tags = r.get("tags", [])
                if tags:
                    lines.append(f"  Tags: {', '.join(tags[:5])}")
            else:
                lines.append(f"")
                lines.append(f"🟢 *AlienVault OTX:* No threats found")

        elif "Port Scan" in source:
            lines.append(f"")
            lines.append(f"🔌 *Port Scan:*")
            lines.append(f"```\n{r.get('data', '')[:500]}\n```")

    return "\n".join(lines)

def format_social_results(username: str, results: List[Dict]) -> str:
    lines = [
        f"🕵 *OSINT — Social Networks*",
        f"",
        f"🎯 Target: `{username}`",
        f"",
    ]
    found = [r for r in results if r.get("found") is True]
    not_found = [r for r in results if r.get("found") is False]

    lines.append(f"✅ Found on {len(found)} platforms")
    lines.append(f"❌ Not found on {len(not_found)} platforms")
    lines.append(f"")

    for r in found:
        platform = r.get("platform", "")
        url = r.get("url", "")
        lines.append(f"🟢 *{platform}*: [Profile]({url})")

        if platform == "GitHub":
            if r.get("name"): lines.append(f"  Name: {r['name']}")
            if r.get("bio"): lines.append(f"  Bio: {r['bio'][:80]}")
            if r.get("location"): lines.append(f"  Location: {r['location']}")
            if r.get("email"): lines.append(f"  Email: {r['email']}")
            if r.get("company"): lines.append(f"  Company: {r['company']}")
            lines.append(f"  Repos: {r.get('public_repos', 0)} | Followers: {r.get('followers', 0)}")
            if r.get("twitter"): lines.append(f"  Twitter: @{r['twitter']}")
            if r.get("top_repos"):
                lines.append(f"  Top repos:")
                for repo in r["top_repos"][:3]:
                    lines.append(f"    ⭐{repo['stars']} [{repo['name']}] {repo.get('description', '')[:40]}")

        elif platform == "Reddit":
            lines.append(f"  Post karma: {r.get('karma_post', 0)} | Comment karma: {r.get('karma_comment', 0)}")
            if r.get("is_mod"): lines.append(f"  ✅ Moderator")
            if r.get("is_gold"): lines.append(f"  ✅ Gold member")

        elif platform in ["Twitter/X", "Instagram", "TikTok", "YouTube"]:
            if r.get("description"): lines.append(f"  Bio: {r['description'][:100]}")

        elif platform == "Telegram":
            if r.get("title"): lines.append(f"  Name: {r['title']}")
            if r.get("subscribers"): lines.append(f"  {r['subscribers']}")
            if r.get("description"): lines.append(f"  About: {r['description'][:80]}")

        elif platform == "VK":
            if r.get("title"): lines.append(f"  Name: {r['title']}")

        elif platform == "Steam":
            if r.get("display_name"): lines.append(f"  Name: {r['display_name']}")

        lines.append(f"")

    if not_found:
        lines.append(f"*Not found:*")
        lines.append(", ".join(r.get("platform", "") for r in not_found))

    return "\n".join(lines)
