import logging, json, os, secrets, time
from pathlib import Path
from eth_account import Account

logger = logging.getLogger("noira1m.wallets")
DATA_DIR = Path(__file__).parent.parent / "data"

def generate_wallets(count: int = 10) -> list:
    path = DATA_DIR / "testnet_wallets.json"
    try:
        with open(path) as f:
            existing = json.load(f)
    except:
        existing = []
    
    generated = 0
    for _ in range(count):
        private_key = "0x" + secrets.token_hex(32)
        account = Account.from_key(private_key)
        existing.append({
            "address": account.address,
            "private_key": private_key,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "balance": "0",
            "tx_count": 0,
        })
        generated += 1
    
    with open(path, "w") as f:
        json.dump(existing, f, indent=2)
    logger.info(f"Generated {generated} wallets (total: {len(existing)})")
    return existing

def get_unused_wallets(limit: int = 5) -> list:
    try:
        with open(DATA_DIR / "testnet_wallets.json") as f:
            wallets = json.load(f)
    except:
        wallets = []
    
    unused = [w for w in wallets if w.get("tx_count", 0) == 0]
    return unused[:limit]

def mark_used(address: str, tx_hash: str = ""):
    path = DATA_DIR / "testnet_wallets.json"
    try:
        with open(path) as f:
            wallets = json.load(f)
    except:
        return
    for w in wallets:
        if w["address"].lower() == address.lower():
            w["tx_count"] = w.get("tx_count", 0) + 1
            if "transactions" not in w:
                w["transactions"] = []
            if tx_hash:
                w["transactions"].append(tx_hash)
            break
    with open(path, "w") as f:
        json.dump(wallets, f, indent=2)
