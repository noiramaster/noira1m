import logging, requests, time, json
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger("noira1m.faucets")

USER_WALLET = "0x435c70c3a509A9277659D838592a993deE296aD6"
DATA_DIR = Path(__file__).parent.parent / "data"

FAUCETS = [
    # Testnet faucets (ETH gratis, sin valor real, pero permite testnet farming -> airdrops)
    {"name": "QuickNodeSepolia", "url": f"https://faucet.quicknode.com/ethereum/sepolia/{USER_WALLET}", "method": "GET", "interval_hours": 24},
    {"name": "AlchemySepolia", "url": f"https://www.infura.io/faucet/sepolia/{USER_WALLET}", "method": "GET", "interval_hours": 24},
    {"name": "BNBTestnet", "url": "https://testnet.bnbchain.org/faucet-smart", "method": "POST", "data": {"address": USER_WALLET}, "interval_hours": 24},
    {"name": "PolygonMumbai", "url": "https://faucet.polygon.technology/", "method": "POST", "data": {"address": USER_WALLET}, "interval_hours": 24},
    # Faucets reales (intentan pagar crypto real)
    {"name": "FreeDoge", "url": f"https://freedogecoin.com/api/claim?wallet={USER_WALLET}", "method": "GET", "interval_hours": 4},
    {"name": "FreeTron", "url": f"https://freetron.io/api/claim?wallet={USER_WALLET}", "method": "GET", "interval_hours": 12},
]

class FaucetManager:
    def __init__(self):
        self.claims_file = DATA_DIR / "faucet_claims.json"
        self.claims = self._load()

    def _load(self):
        try:
            with open(self.claims_file) as f:
                return json.load(f)
        except:
            return {}

    def _save(self):
        with open(self.claims_file, "w") as f:
            json.dump(self.claims, f, indent=2)

    def can_claim(self, name, interval):
        last = self.claims.get(name)
        if not last:
            return True
        elapsed = (datetime.now(timezone.utc) - datetime.fromisoformat(last)).total_seconds() / 3600
        return elapsed >= interval

    def claim_all(self):
        results = []
        for f in FAUCETS:
            if not self.can_claim(f["name"], f["interval_hours"]):
                results.append({"faucet": f["name"], "status": "cooldown"})
                continue
            try:
                if f["method"] == "POST":
                    data = f.get("data", {"address": USER_WALLET})
                    resp = requests.post(f["url"], json=data, timeout=15)
                else:
                    resp = requests.get(f["url"], timeout=15)
                
                if resp.status_code == 200:
                    self.claims[f["name"]] = datetime.now(timezone.utc).isoformat()
                    self._save()
                    results.append({"faucet": f["name"], "status": "claimed"})
                    logger.info(f"Faucet claimed: {f['name']}")
                else:
                    results.append({"faucet": f["name"], "status": f"HTTP {resp.status_code}"})
            except Exception as e:
                results.append({"faucet": f["name"], "status": f"error {str(e)[:40]}"})
            time.sleep(2)
        return results

def run():
    fm = FaucetManager()
    return fm.claim_all()
