import logging, requests, time, re
from datetime import datetime, timezone

logger = logging.getLogger("noira1m.rss")

FEEDS = [
    {"url": "https://cointelegraph.com/rss", "name": "CoinTelegraph"},
    {"url": "https://www.coindesk.com/arc/outboundfeeds/rss/", "name": "CoinDesk"},
    {"url": "https://cryptopotato.com/feed/", "name": "CryptoPotato"},
    {"url": "https://cryptoslate.com/feed/", "name": "CryptoSlate"},
    {"url": "https://thecryptobasic.com/feed/", "name": "CryptoBasic"},
    {"url": "https://www.newsbtc.com/feed/", "name": "NewsBTC"},
    {"url": "https://bitcoinmagazine.com/.rss/full/", "name": "BitcoinMag"},
    {"url": "https://blockworks.co/feed", "name": "Blockworks"},
    {"url": "https://defiant.io/feed.xml", "name": "Defiant"},
    {"url": "https://rekt.news/feed.xml", "name": "Rekt"},
]

KEYWORD_PATTERNS = [
    r"airdrop", r"token launch", r"token distribution", r"claim", r"retroactive",
    r"livenet", r"mainnet launch", r"token generation", r"tge", r"farming",
    r"testnet", r"points program", r"loyalty points", r"reward",
]

def scan() -> list:
    results = []
    import xml.etree.ElementTree as ET
    for feed in FEEDS:
        try:
            resp = requests.get(feed["url"], timeout=10)
            if resp.status_code != 200:
                continue
            root = ET.fromstring(resp.content)
            items = []
            for item in root.findall(".//item"):
                title = item.findtext("title", "")
                desc = item.findtext("description", "")
                link = item.findtext("link", "")
                pub_date = item.findtext("pubDate", "")
                text = f"{title} {desc}".lower()
                for pattern in KEYWORD_PATTERNS:
                    if re.search(pattern, text):
                        items.append({
                            "source": feed["name"],
                            "title": title.strip(),
                            "desc": desc.strip()[:150],
                            "url": link.strip(),
                            "found_at": datetime.now(timezone.utc).isoformat(),
                        })
                        break
            results.extend(items)
            time.sleep(0.5)
        except Exception as e:
            logger.debug(f"RSS error {feed['name']}: {e}")
    logger.info(f"RSS: found {len(results)} opportunities")
    return results
