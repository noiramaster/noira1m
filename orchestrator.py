import logging, json, time
from datetime import datetime, timezone
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("noira1m")

BASE = Path(__file__).parent
DATA = BASE / "data"
DATA.mkdir(exist_ok=True)

def save(name, data):
    (DATA / f"{name}.json").write_text(json.dumps(data, indent=2, default=str))

import requests, xml.etree.ElementTree as ET, re

WALLET = "0x435c70c3a509A9277659D838592a993deE296aD6"

def run():
    results = {}

    # 1. Airdrop scan RSS
    feeds = [
        ("CoinTelegraph", "https://cointelegraph.com/rss"),
        ("CryptoPotato", "https://cryptopotato.com/feed/"),
        ("CryptoSlate", "https://cryptoslate.com/feed/"),
        ("NewsBTC", "https://www.newsbtc.com/feed/"),
        ("Blockworks", "https://blockworks.co/feed"),
    ]
    keywords = ["airdrop", "claim", "retroactive", "testnet", "farming", "points", "reward", "launch", "token"]
    ads = []
    for name, url in feeds:
        try:
            r = requests.get(url, timeout=10)
            root = ET.fromstring(r.content)
            for item in root.findall(".//item")[:10]:
                t = (item.findtext("title","") + " " + item.findtext("description","")).lower()
                link = item.findtext("link","")
                for kw in keywords:
                    if kw in t:
                        ads.append({"source":name, "title":item.findtext("title","").strip(), "url":link.strip()})
                        break
        except Exception as e:
            logger.debug(f"RSS {name}: {e}")
    save("airdrops", ads)
    results["airdrops"] = len(ads)
    logger.info(f"Airdrops: {len(ads)}")

    # 2. Wallet generation
    try:
        from eth_account import Account
        import secrets
        wallets_path = DATA / "testnet_wallets.json"
        try:
            wallets = json.loads(wallets_path.read_text())
        except:
            wallets = []
        for _ in range(5):
            pk = "0x" + secrets.token_hex(32)
            wallets.append({"address": Account.from_key(pk).address, "created": datetime.now(timezone.utc).isoformat()})
        wallets_path.write_text(json.dumps(wallets, indent=2))
        results["wallets"] = len(wallets)
        logger.info(f"Wallets: {len(wallets)} total")
    except Exception as e:
        logger.warning(f"Wallet error: {e}")
        results["wallets"] = f"error: {str(e)[:40]}"

    # 3. Web scrape
    sites = [
        ("Airdrops.io", "https://airdrops.io/"),
        ("DeFiLlama", "https://defillama.com/airdrops"),
        ("CoinGecko", "https://www.coingecko.com/en/airdrops"),
    ]
    web = []
    for name, url in sites:
        try:
            r = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            web.append({"source": name, "found_airdrop_keywords": any(k in r.text.lower() for k in ["airdrop","claim","free token"])})
        except:
            pass
    save("web", web)
    results["web"] = len(web)
    logger.info(f"Web: {len(web)}")

    # 4. Check wallet for known airdrops (Uniswap, ENS, etc.)
    checks = {
        "Uniswap": f"https://api.uniswap.org/airdrop/check/{WALLET}",
    }
    for name, url in checks.items():
        try:
            r = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            results[f"check_{name}"] = f"HTTP {r.status_code}"
        except Exception as e:
            results[f"check_{name}"] = f"error"

    results["wallet"] = WALLET[:10] + "..."
    results["timestamp"] = datetime.now(timezone.utc).isoformat()
    
    save("last_run", results)
    logger.info(f"Done: {json.dumps({k:v for k,v in results.items() if k!='wallet'})}")

if __name__ == "__main__":
    run()
