import logging, requests, time, json
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger("noira1m.faucets")

FAUCETS = [
    {"name": "FreeBNS", "url": "https://freebns.com/api/claim", "coin": "BNB", "interval_hours": 24},
    {"name": "FreeTRX", "url": "https://freedoge.com/api/claim", "coin": "TRX", "interval_hours": 1},
    {"name": "FreeBTC", "url": "https://freebitco.in/api/claim", "coin": "BTC", "interval_hours": 1},
]

class FaucetManager:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.claims_file = f"{data_dir}/faucet_claims.json"
        self.claims = self._load_claims()

    def _load_claims(self) -> dict:
        try:
            with open(self.claims_file) as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save_claims(self):
        with open(self.claims_file, "w") as f:
            json.dump(self.claims, f, indent=2)

    def can_claim(self, faucet_name: str, interval_hours: int) -> bool:
        last = self.claims.get(faucet_name)
        if not last:
            return True
        elapsed = (datetime.now(timezone.utc) - datetime.fromisoformat(last)).total_seconds() / 3600
        return elapsed >= interval_hours

    def claim_all(self) -> list:
        results = []
        for faucet in FAUCETS:
            if not self.can_claim(faucet["name"], faucet["interval_hours"]):
                results.append({"faucet": faucet["name"], "status": "cooldown"})
                continue
            try:
                resp = requests.post(faucet["url"], timeout=15)
                if resp.status_code == 200:
                    self.claims[faucet["name"]] = datetime.now(timezone.utc).isoformat()
                    self._save_claims()
                    results.append({"faucet": faucet["name"], "status": "claimed", "response": resp.text[:100]})
                    logger.info(f"Claimed {faucet['name']}")
                else:
                    results.append({"faucet": faucet["name"], "status": f"error HTTP {resp.status_code}"})
            except Exception as e:
                results.append({"faucet": faucet["name"], "status": f"error {str(e)[:50]}"})
            time.sleep(2)
        return results
