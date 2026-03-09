"""
Sites Database - fetches real site lists from WhatsMyName & Sherlock GitHub repos.
Supports 500+ websites for username enumeration.
"""
import asyncio
import aiohttp
import json
import logging
from typing import List, Dict
from pathlib import Path

logger = logging.getLogger(__name__)

CACHE_FILE = Path(__file__).parent.parent / "data" / "sites_cache.json"
CACHE_FILE.parent.mkdir(exist_ok=True)

# WhatsMyName project - community maintained, 500+ sites
WHATSMYNAME_URL = "https://raw.githubusercontent.com/WebBreacher/WhatsMyName/main/wmn-data.json"

# Sherlock project sites list
SHERLOCK_URL = "https://raw.githubusercontent.com/sherlock-project/sherlock/master/sherlock/resources/data.json"

# Fallback hardcoded list (critical sites, always available)
FALLBACK_SITES = [
    {"name": "GitHub", "uri_check": "https://github.com/{}", "e_code": 200, "e_string": ""},
    {"name": "Twitter/X", "uri_check": "https://x.com/{}", "e_code": 200, "e_string": ""},
    {"name": "Instagram", "uri_check": "https://www.instagram.com/{}/", "e_code": 200, "e_string": ""},
    {"name": "Reddit", "uri_check": "https://www.reddit.com/user/{}", "e_code": 200, "e_string": ""},
    {"name": "TikTok", "uri_check": "https://www.tiktok.com/@{}", "e_code": 200, "e_string": ""},
    {"name": "YouTube", "uri_check": "https://www.youtube.com/@{}", "e_code": 200, "e_string": ""},
    {"name": "LinkedIn", "uri_check": "https://www.linkedin.com/in/{}", "e_code": 200, "e_string": ""},
    {"name": "Pinterest", "uri_check": "https://www.pinterest.com/{}/", "e_code": 200, "e_string": ""},
    {"name": "Twitch", "uri_check": "https://www.twitch.tv/{}", "e_code": 200, "e_string": ""},
    {"name": "Steam", "uri_check": "https://steamcommunity.com/id/{}", "e_code": 200, "e_string": ""},
    {"name": "Telegram", "uri_check": "https://t.me/{}", "e_code": 200, "e_string": ""},
    {"name": "GitLab", "uri_check": "https://gitlab.com/{}", "e_code": 200, "e_string": ""},
    {"name": "Bitbucket", "uri_check": "https://bitbucket.org/{}", "e_code": 200, "e_string": ""},
    {"name": "Medium", "uri_check": "https://medium.com/@{}", "e_code": 200, "e_string": ""},
    {"name": "Dev.to", "uri_check": "https://dev.to/{}", "e_code": 200, "e_string": ""},
    {"name": "Patreon", "uri_check": "https://www.patreon.com/{}", "e_code": 200, "e_string": ""},
    {"name": "Keybase", "uri_check": "https://keybase.io/{}", "e_code": 200, "e_string": ""},
    {"name": "Flickr", "uri_check": "https://www.flickr.com/people/{}", "e_code": 200, "e_string": ""},
    {"name": "Vimeo", "uri_check": "https://vimeo.com/{}", "e_code": 200, "e_string": ""},
    {"name": "SoundCloud", "uri_check": "https://soundcloud.com/{}", "e_code": 200, "e_string": ""},
    {"name": "Spotify", "uri_check": "https://open.spotify.com/user/{}", "e_code": 200, "e_string": ""},
    {"name": "HackerNews", "uri_check": "https://news.ycombinator.com/user?id={}", "e_code": 200, "e_string": ""},
    {"name": "ProductHunt", "uri_check": "https://www.producthunt.com/@{}", "e_code": 200, "e_string": ""},
    {"name": "Gravatar", "uri_check": "https://en.gravatar.com/{}", "e_code": 200, "e_string": ""},
    {"name": "About.me", "uri_check": "https://about.me/{}", "e_code": 200, "e_string": ""},
    {"name": "Behance", "uri_check": "https://www.behance.net/{}", "e_code": 200, "e_string": ""},
    {"name": "Dribbble", "uri_check": "https://dribbble.com/{}", "e_code": 200, "e_string": ""},
    {"name": "CodePen", "uri_check": "https://codepen.io/{}", "e_code": 200, "e_string": ""},
    {"name": "Replit", "uri_check": "https://replit.com/@{}", "e_code": 200, "e_string": ""},
    {"name": "HackerRank", "uri_check": "https://www.hackerrank.com/{}", "e_code": 200, "e_string": ""},
    {"name": "LeetCode", "uri_check": "https://leetcode.com/{}", "e_code": 200, "e_string": ""},
    {"name": "Codeforces", "uri_check": "https://codeforces.com/profile/{}", "e_code": 200, "e_string": ""},
    {"name": "npm", "uri_check": "https://www.npmjs.com/~{}", "e_code": 200, "e_string": ""},
    {"name": "PyPI", "uri_check": "https://pypi.org/user/{}/", "e_code": 200, "e_string": ""},
    {"name": "DockerHub", "uri_check": "https://hub.docker.com/u/{}", "e_code": 200, "e_string": ""},
    {"name": "Quora", "uri_check": "https://www.quora.com/profile/{}", "e_code": 200, "e_string": ""},
    {"name": "Tumblr", "uri_check": "https://{}.tumblr.com", "e_code": 200, "e_string": ""},
    {"name": "WordPress", "uri_check": "https://{}.wordpress.com", "e_code": 200, "e_string": ""},
    {"name": "Blogger", "uri_check": "https://{}.blogspot.com", "e_code": 200, "e_string": ""},
    {"name": "itch.io", "uri_check": "https://{}.itch.io", "e_code": 200, "e_string": ""},
    {"name": "Chess.com", "uri_check": "https://www.chess.com/member/{}", "e_code": 200, "e_string": ""},
    {"name": "Lichess", "uri_check": "https://lichess.org/@/{}", "e_code": 200, "e_string": ""},
    {"name": "Goodreads", "uri_check": "https://www.goodreads.com/{}", "e_code": 200, "e_string": ""},
    {"name": "AngelList", "uri_check": "https://angel.co/u/{}", "e_code": 200, "e_string": ""},
    {"name": "Fiverr", "uri_check": "https://www.fiverr.com/{}", "e_code": 200, "e_string": ""},
    {"name": "Upwork", "uri_check": "https://www.upwork.com/freelancers/~{}", "e_code": 200, "e_string": ""},
    {"name": "Freelancer", "uri_check": "https://www.freelancer.com/u/{}", "e_code": 200, "e_string": ""},
    {"name": "Kickstarter", "uri_check": "https://www.kickstarter.com/profile/{}", "e_code": 200, "e_string": ""},
    {"name": "Indiegogo", "uri_check": "https://www.indiegogo.com/individuals/{}", "e_code": 200, "e_string": ""},
    {"name": "Bandcamp", "uri_check": "https://bandcamp.com/{}", "e_code": 200, "e_string": ""},
    {"name": "Last.fm", "uri_check": "https://www.last.fm/user/{}", "e_code": 200, "e_string": ""},
    {"name": "Mixcloud", "uri_check": "https://www.mixcloud.com/{}/", "e_code": 200, "e_string": ""},
    {"name": "ReverbNation", "uri_check": "https://www.reverbnation.com/{}", "e_code": 200, "e_string": ""},
    {"name": "Letterboxd", "uri_check": "https://letterboxd.com/{}", "e_code": 200, "e_string": ""},
    {"name": "Trakt", "uri_check": "https://trakt.tv/users/{}", "e_code": 200, "e_string": ""},
    {"name": "Twitch Clips", "uri_check": "https://clips.twitch.tv/{}", "e_code": 200, "e_string": ""},
    {"name": "Periscope", "uri_check": "https://www.periscope.tv/{}", "e_code": 200, "e_string": ""},
    {"name": "Etsy", "uri_check": "https://www.etsy.com/shop/{}", "e_code": 200, "e_string": ""},
    {"name": "eBay", "uri_check": "https://www.ebay.com/usr/{}", "e_code": 200, "e_string": ""},
    {"name": "Gumroad", "uri_check": "https://{}.gumroad.com", "e_code": 200, "e_string": ""},
    {"name": "Substack", "uri_check": "https://{}.substack.com", "e_code": 200, "e_string": ""},
    {"name": "Buy Me a Coffee", "uri_check": "https://www.buymeacoffee.com/{}", "e_code": 200, "e_string": ""},
    {"name": "Ko-fi", "uri_check": "https://ko-fi.com/{}", "e_code": 200, "e_string": ""},
    {"name": "Linktree", "uri_check": "https://linktr.ee/{}", "e_code": 200, "e_string": ""},
    {"name": "Carrd", "uri_check": "https://{}.carrd.co", "e_code": 200, "e_string": ""},
    {"name": "Notion", "uri_check": "https://notion.so/@{}", "e_code": 200, "e_string": ""},
    {"name": "Loom", "uri_check": "https://www.loom.com/share/{}", "e_code": 200, "e_string": ""},
    {"name": "Snapchat", "uri_check": "https://www.snapchat.com/add/{}", "e_code": 200, "e_string": ""},
    {"name": "VSCO", "uri_check": "https://vsco.co/{}", "e_code": 200, "e_string": ""},
    {"name": "500px", "uri_check": "https://500px.com/p/{}", "e_code": 200, "e_string": ""},
    {"name": "Unsplash", "uri_check": "https://unsplash.com/@{}", "e_code": 200, "e_string": ""},
    {"name": "WikiData", "uri_check": "https://www.wikidata.org/wiki/User:{}", "e_code": 200, "e_string": ""},
    {"name": "Wikipedia", "uri_check": "https://en.wikipedia.org/wiki/User:{}", "e_code": 200, "e_string": ""},
    {"name": "SourceForge", "uri_check": "https://sourceforge.net/u/{}/profile", "e_code": 200, "e_string": ""},
    {"name": "Launchpad", "uri_check": "https://launchpad.net/~{}", "e_code": 200, "e_string": ""},
    {"name": "Disqus", "uri_check": "https://disqus.com/by/{}/", "e_code": 200, "e_string": ""},
    {"name": "Foursquare", "uri_check": "https://foursquare.com/{}", "e_code": 200, "e_string": ""},
    {"name": "ResearchGate", "uri_check": "https://www.researchgate.net/profile/{}", "e_code": 200, "e_string": ""},
    {"name": "Academia.edu", "uri_check": "https://independent.academia.edu/{}", "e_code": 200, "e_string": ""},
    {"name": "SlideShare", "uri_check": "https://www.slideshare.net/{}", "e_code": 200, "e_string": ""},
    {"name": "Scribd", "uri_check": "https://www.scribd.com/{}", "e_code": 200, "e_string": ""},
    {"name": "Crunchbase", "uri_check": "https://www.crunchbase.com/person/{}", "e_code": 200, "e_string": ""},
    {"name": "F6S", "uri_check": "https://www.f6s.com/{}", "e_code": 200, "e_string": ""},
    {"name": "Xing", "uri_check": "https://www.xing.com/profile/{}", "e_code": 200, "e_string": ""},
    {"name": "VK", "uri_check": "https://vk.com/{}", "e_code": 200, "e_string": ""},
    {"name": "OK.ru", "uri_check": "https://ok.ru/{}", "e_code": 200, "e_string": ""},
    {"name": "Habr", "uri_check": "https://habr.com/en/users/{}/", "e_code": 200, "e_string": ""},
    {"name": "My.mail.ru", "uri_check": "https://my.mail.ru/mail/{}", "e_code": 200, "e_string": ""},
    {"name": "Livejournal", "uri_check": "https://{}.livejournal.com", "e_code": 200, "e_string": ""},
    {"name": "Ask.fm", "uri_check": "https://ask.fm/{}", "e_code": 200, "e_string": ""},
    {"name": "Wattpad", "uri_check": "https://www.wattpad.com/user/{}", "e_code": 200, "e_string": ""},
    {"name": "Fanfiction.net", "uri_check": "https://www.fanfiction.net/u/{}", "e_code": 200, "e_string": ""},
    {"name": "ArchiveOfOurOwn", "uri_check": "https://archiveofourown.org/users/{}", "e_code": 200, "e_string": ""},
    {"name": "Roblox", "uri_check": "https://www.roblox.com/user.aspx?username={}", "e_code": 200, "e_string": ""},
    {"name": "Minecraft", "uri_check": "https://namemc.com/profile/{}", "e_code": 200, "e_string": ""},
    {"name": "Fortnite Tracker", "uri_check": "https://fortnitetracker.com/profile/all/{}", "e_code": 200, "e_string": ""},
    {"name": "Apex Tracker", "uri_check": "https://apex.tracker.gg/apex/profile/origin/{}", "e_code": 200, "e_string": ""},
    {"name": "Overwatch", "uri_check": "https://playoverwatch.com/en-us/career/pc/{}/", "e_code": 200, "e_string": ""},
    {"name": "Xbox Gamertag", "uri_check": "https://xboxgamertag.com/search/{}", "e_code": 200, "e_string": ""},
    {"name": "PSN Profiles", "uri_check": "https://psnprofiles.com/{}", "e_code": 200, "e_string": ""},
    {"name": "Twitch Tracker", "uri_check": "https://twitchtracker.com/{}", "e_code": 200, "e_string": ""},
    {"name": "StreamElements", "uri_check": "https://streamelements.com/{}/tips", "e_code": 200, "e_string": ""},
    {"name": "Streamlabs", "uri_check": "https://streamlabs.com/{}", "e_code": 200, "e_string": ""},
    {"name": "DLive", "uri_check": "https://dlive.tv/{}", "e_code": 200, "e_string": ""},
    {"name": "Rumble", "uri_check": "https://rumble.com/user/{}", "e_code": 200, "e_string": ""},
    {"name": "Odysee", "uri_check": "https://odysee.com/@{}", "e_code": 200, "e_string": ""},
    {"name": "BitChute", "uri_check": "https://www.bitchute.com/channel/{}/", "e_code": 200, "e_string": ""},
    {"name": "Dailymotion", "uri_check": "https://www.dailymotion.com/{}", "e_code": 200, "e_string": ""},
    {"name": "Veoh", "uri_check": "https://www.veoh.com/users/{}", "e_code": 200, "e_string": ""},
    {"name": "Minds", "uri_check": "https://www.minds.com/{}", "e_code": 200, "e_string": ""},
    {"name": "Gab", "uri_check": "https://gab.com/{}", "e_code": 200, "e_string": ""},
    {"name": "Mastodon Social", "uri_check": "https://mastodon.social/@{}", "e_code": 200, "e_string": ""},
    {"name": "Diaspora", "uri_check": "https://diaspora.social/{}", "e_code": 200, "e_string": ""},
    {"name": "MeWe", "uri_check": "https://mewe.com/i/{}", "e_code": 200, "e_string": ""},
    {"name": "Parler", "uri_check": "https://parler.com/{}", "e_code": 200, "e_string": ""},
    {"name": "CounterSocial", "uri_check": "https://counter.social/@{}", "e_code": 200, "e_string": ""},
    {"name": "HiveSocial", "uri_check": "https://hivesocial.app/user/{}", "e_code": 200, "e_string": ""},
    {"name": "Cohost", "uri_check": "https://cohost.org/{}", "e_code": 200, "e_string": ""},
    {"name": "Bluesky", "uri_check": "https://bsky.app/profile/{}", "e_code": 200, "e_string": ""},
    {"name": "Truth Social", "uri_check": "https://truthsocial.com/@{}", "e_code": 200, "e_string": ""},
    {"name": "Clubhouse", "uri_check": "https://www.clubhouse.com/@{}", "e_code": 200, "e_string": ""},
    {"name": "BeReal", "uri_check": "https://bere.al/{}", "e_code": 200, "e_string": ""},
    {"name": "Threads", "uri_check": "https://www.threads.net/@{}", "e_code": 200, "e_string": ""},
]

async def fetch_whatsmyname_sites() -> List[Dict]:
    """Fetch 500+ sites from WhatsMyName project."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(WHATSMYNAME_URL, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 200:
                    data = await resp.json(content_type=None)
                    sites = []
                    for site in data.get("sites", []):
                        if site.get("uri_check") and site.get("e_code"):
                            sites.append({
                                "name": site.get("name", ""),
                                "uri_check": site.get("uri_check", ""),
                                "e_code": site.get("e_code", 200),
                                "e_string": site.get("e_string", ""),
                                "m_string": site.get("m_string", ""),
                            })
                    if len(sites) > 50:
                        logger.info(f"Loaded {len(sites)} sites from WhatsMyName")
                        return sites
    except Exception as e:
        logger.warning(f"WhatsMyName fetch failed: {e}")
    return []

async def fetch_sherlock_sites() -> List[Dict]:
    """Fetch sites from Sherlock project."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(SHERLOCK_URL, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 200:
                    data = await resp.json(content_type=None)
                    sites = []
                    for name, info in data.items():
                        url = info.get("url", "")
                        if "{}" not in url and "{}" not in url:
                            url = url.replace("{}", "{}")
                        sites.append({
                            "name": name,
                            "uri_check": url,
                            "e_code": 200,
                            "e_string": info.get("errorType", ""),
                            "m_string": "",
                        })
                    logger.info(f"Loaded {len(sites)} sites from Sherlock")
                    return sites
    except Exception as e:
        logger.warning(f"Sherlock fetch failed: {e}")
    return []

async def get_sites_list() -> List[Dict]:
    """Get combined sites list from all sources + cache."""
    # Try cache first
    if CACHE_FILE.exists():
        try:
            import time
            age = time.time() - CACHE_FILE.stat().st_mtime
            if age < 86400:  # 24h cache
                with open(CACHE_FILE) as f:
                    cached = json.load(f)
                    if len(cached) > 100:
                        return cached
        except Exception:
            pass

    # Fetch fresh
    wmn_sites, sherlock_sites = await asyncio.gather(
        fetch_whatsmyname_sites(),
        fetch_sherlock_sites(),
    )

    # Merge: WMN primary + fallback + sherlock
    seen_names = set()
    combined = []

    for site in wmn_sites:
        n = site["name"].lower()
        if n not in seen_names:
            seen_names.add(n)
            combined.append(site)

    for site in FALLBACK_SITES:
        n = site["name"].lower()
        if n not in seen_names:
            seen_names.add(n)
            combined.append(site)

    for site in sherlock_sites:
        n = site["name"].lower()
        if n not in seen_names and "{}" in site.get("uri_check", ""):
            seen_names.add(n)
            combined.append(site)

    # Save cache
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(combined, f)
    except Exception:
        pass

    return combined if combined else FALLBACK_SITES
