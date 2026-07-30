import logging, requests, time, re
from datetime import datetime, timezone

logger = logging.getLogger("noira1m.web")

SITES = [
    {"url": "https://airdrops.io/", "name": "Airdrops.io"},
    {"url": "https://blog.thirdweb.com/tag/airdrop/", "name": "Thirdweb"},
    {"url": "https://defillama.com/airdrops", "name": "DeFiLlama"},
    {"url": "https://www.coingecko.com/en/discover/airdrops", "name": "CoinGecko"},
    {"url": "https://galxe.com/", "name": "Galxe"},
    {"url": "https://layer3.xyz/", "name": "Layer3"},
    {"url": "https://rabbithole.gg/", "name": "RabbitHole"},
]

def scan() -> list:
    results = []
    for site in SITES:
        try:
            resp = requests.get(site["url"], timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code != 200:
                continue
            text = resp.text.lower()
            keywords = ["airdrop", "claim now", "free tokens", "reward", "farming"]
            found = [k for k in keywords if k in text]
            if found:
                results.append({
                    "source": site["name"],
                    "keywords": found,
                    "url": site["url"],
                    "found_at": datetime.now(timezone.utc).isoformat(),
                })
            time.sleep(1)
        except Exception as e:
            logger.debug(f"Web error {site['name']}: {e}")
    logger.info(f"Web: found {len(results)} opportunities")
    return results
