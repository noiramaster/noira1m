import logging, requests, time, re
from datetime import datetime, timezone

logger = logging.getLogger("noira1m.twitter")

CRYPTO_ACCOUNTS = [
    "airdrops", "airdrop_alert", "defiantnews", "TheDeFiEdge",
    "cryptobriefing", "BitcoinMagazine", "cointelegraph", "CoinDesk",
    "rektnews", "zksync", "arbitrum", "optimismFND", "base",
    "LayerZero_Labs", "scroll_zk", "LineaBuild",
]

def scan() -> list:
    results = []
    for account in CRYPTO_ACCOUNTS:
        try:
            resp = requests.get(f"https://nitter.net/{account}/rss", timeout=10)
            if resp.status_code == 200:
                import xml.etree.ElementTree as ET
                root = ET.fromstring(resp.content)
                keywords = ["airdrop", "launch", "token", "claim", "reward", "farming", "testnet", "points"]
                for item in root.findall(".//item")[:5]:
                    title = item.findtext("title", "")
                    link = item.findtext("link", "")
                    text = title.lower()
                    if any(k in text for k in keywords):
                        results.append({
                            "source": f"@{account}",
                            "title": title.strip(),
                            "url": link.strip(),
                            "found_at": datetime.now(timezone.utc).isoformat(),
                        })
            time.sleep(1)
        except Exception as e:
            logger.debug(f"Twitter error @{account}: {e}")
    logger.info(f"Twitter: found {len(results)} opportunities")
    return results
