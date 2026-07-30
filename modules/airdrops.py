import logging, requests, time, json, re
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger("noira1m.airdrops")

SOURCES = [
    {"name": "airdropsio", "url": "https://api.airdrops.io/v1/airdrops", "type": "api"},
    {"name": "airdropalert", "url": "https://airdropalert.com/feed/", "type": "rss"},
    {"name": "cointeligence", "url": "https://cointeligence.com/feed/", "type": "rss"},
]

KNOWN_SCAM_PATTERNS = [
    "send", "deposit", "gas fee", "verification fee", "private key",
    "seed phrase", "connect wallet", "claim with ETH",
]

def fetch_airdrops() -> list:
    airdrops = []
    for source in SOURCES:
        try:
            if source["type"] == "api":
                resp = requests.get(source["url"], timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    items = data.get("data", []) if isinstance(data, dict) and "data" in data else (data if isinstance(data, list) else [])
                    for item in items[:20]:
                        title = item.get("title", item.get("name", ""))
                        desc = item.get("description", item.get("short_description", ""))
                        url = item.get("url", item.get("link", ""))
                        value = item.get("value", item.get("estimated_value", "unknown"))
                        if not _is_scam(f"{title} {desc}"):
                            airdrops.append({"source": source["name"], "title": title,
                                             "description": desc[:200], "url": url,
                                             "value": value, "found_at": datetime.now(timezone.utc).isoformat()})
            time.sleep(1)
        except Exception as e:
            logger.debug(f"Source {source['name']} failed: {e}")
    return airdrops

def _is_scam(text: str) -> bool:
    text_lower = text.lower()
    return any(p in text_lower for p in KNOWN_SCAM_PATTERNS)

def scan_twitter_airdrops() -> list:
    try:
        resp = requests.get("https://api.nitter.net/search", params={"q": "airdrop OR giveway crypto free", "limit": 20}, timeout=10)
        if resp.status_code == 200:
            return [{"source": "twitter", "title": t.get("text", "")[:100],
                     "url": f"https://twitter.com{i}" if (i := t.get("link")) else "",
                     "found_at": datetime.now(timezone.utc).isoformat()}
                    for t in resp.json().get("tweets", [])[:10]]
    except Exception:
        pass
    return []
