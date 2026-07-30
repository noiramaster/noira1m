import logging, requests, time, json
from datetime import datetime, timezone

logger = logging.getLogger("noira1m.faucets")

USER_WALLET = "0x435c70c3a509A9277659D838592a993deE296aD6"

FAUCETS = [
    # Testnet faucets (100% gratis, funcionan con HTTP, ETH sin valor real pero sirven para testnet farming -> airdrops reales)
    {"name": "SepoliaETH", "url": f"https://faucet.quicknode.com/ethereum/sepolia/{USER_WALLET}", "method": "GET", "interval_hours": 24},
    {"name": "SepoliaInfura", "url": f"https://www.infura.io/faucet/sepolia/{USER_WALLET}", "method": "GET", "interval_hours": 24},
    {"name": "GoerliETH", "url": f"https://goerli-faucet.pk910.de/claim/{USER_WALLET}", "method": "GET", "interval_hours": 24},
    {"name": "BNBTestnet", "url": "https://testnet.bnbchain.org/faucet-smart", "wallet_param": "address", "method": "POST", "interval_hours": 24},
    {"name": "MumbaiMATIC", "url": "https://faucet.polygon.technology/", "wallet_param": "address", "method": "POST", "interval_hours": 24},
    {"name": "AvalancheTest", "url": "https://faucet.avax.network/", "wallet_param": "address", "method": "POST", "interval_hours": 24},
    # Faucets reales (algunos funcionan con GET directo)
    {"name": "FreeDogeCoin", "url": f"https://freedogecoin.com/api/claim?wallet={USER_WALLET}", "method": "GET", "interval_hours": 1},
    {"name": "FreeBitcoin", "url": f"https://freebitco.in/api/claim?wallet={USER_WALLET}", "method": "GET", "interval_hours": 1},
    {"name": "FreeTron", "url": f"https://freetron.io/api/claim?wallet={USER_WALLET}", "method": "GET", "interval_hours": 12},
    {"name": "FreeSolana", "url": f"https://freesolana.io/api/claim?wallet={USER_WALLET}", "method": "GET", "interval_hours": 12},
]

class FaucetManager:
    def __init__(self, data_dir: str = "data"):
        self.claims_file = f"{data_dir}/faucet_claims.json"
        self.claims = self._load()

    def _load(self) -> dict:
        try:
            with open(self.claims_file) as f:
                return json.load(f)
        except:
            return {}

    def _save(self):
        with open(self.claims_file, "w") as f:
            json.dump(self.claims, f, indent=2)

    def can_claim(self, name: str, interval: int) -> bool:
        last = self.claims.get(name)
        if not last:
            return True
        elapsed = (datetime.now(timezone.utc) - datetime.fromisoformat(last)).total_seconds() / 3600
        return elapsed >= interval

    def claim_all(self) -> list:
        results = []
        for faucet in FAUCETS:
            if not self.can_claim(faucet["name"], faucet["interval_hours"]):
                results.append({"faucet": faucet["name"], "status": "cooldown"})
                continue
            try:
                if faucet["method"] == "POST":
                    wallet = faucet.get("wallet_param", "address")
                    resp = requests.post(faucet["url"], json={wallet: USER_WALLET}, timeout=15)
                else:
                    resp = requests.get(faucet["url"], timeout=15)

                if resp.status_code == 200:
                    self.claims[faucet["name"]] = datetime.now(timezone.utc).isoformat()
                    self._save()
                    results.append({"faucet": faucet["name"], "status": "claimed", "response": resp.text[:100]})
                    logger.info(f"Claimed {faucet['name']}")
                else:
                    results.append({"faucet": faucet["name"], "status": f"HTTP {resp.status_code}"})
                    logger.debug(f"Failed {faucet['name']}: HTTP {resp.status_code}")
            except Exception as e:
                results.append({"faucet": faucet["name"], "status": f"error {str(e)[:50]}"})
            time.sleep(2)
        return results
