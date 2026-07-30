import logging, json, time
from datetime import datetime, timezone
from pathlib import Path
from playwright.sync_api import sync_playwright

logger = logging.getLogger("noira1m.claimer")

USER_WALLET = "0x435c70c3a509A9277659D838592a993deE296aD6"
DATA_DIR = Path(__file__).parent.parent / "data"

FAUCET_SITES = [
    {"name": "FreeBTC", "url": "https://freebitco.in", "wallet_selector": "#addy", "claim_selector": "#claim", "captcha_selector": ".captcha", "interval_hours": 1},
    {"name": "FreeDoge", "url": "https://freedogecoin.com", "wallet_selector": "[name=wallet]", "claim_selector": "[type=submit]", "captcha_selector": "", "interval_hours": 1},
    {"name": "FreeBNB", "url": "https://freebnb.app", "wallet_selector": "[name=address]", "claim_selector": "#claim", "captcha_selector": "", "interval_hours": 24},
    {"name": "FreeTRX", "url": "https://tronfaucet.io", "wallet_selector": "[name=wallet]", "claim_selector": "[type=submit]", "captcha_selector": "", "interval_hours": 12},
    {"name": "FreeMATIC", "url": "https://maticfaucet.app", "wallet_selector": "[name=address]", "claim_selector": "#claim", "captcha_selector": "", "interval_hours": 24},
]

class FaucetClaimer:
    def __init__(self):
        self.claims_file = DATA_DIR / "playwright_claims.json"
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
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                viewport={"width": 1280, "height": 720},
            )
            for site in FAUCET_SITES:
                if not self.can_claim(site["name"], site["interval_hours"]):
                    results.append({"faucet": site["name"], "status": "cooldown"})
                    continue
                try:
                    page = context.new_page()
                    page.goto(site["url"], timeout=30000)
                    time.sleep(2)

                    if site.get("wallet_selector"):
                        try:
                            page.fill(site["wallet_selector"], USER_WALLET, timeout=5000)
                        except:
                            pass

                    if site.get("captcha_selector"):
                        try:
                            captcha = page.query_selector(site["captcha_selector"])
                            if captcha:
                                captcha.click()
                                time.sleep(1)
                        except:
                            pass

                    if site.get("claim_selector"):
                        try:
                            page.click(site["claim_selector"], timeout=5000)
                            time.sleep(2)
                        except:
                            pass

                    self.claims[site["name"]] = datetime.now(timezone.utc).isoformat()
                    self._save()
                    results.append({"faucet": site["name"], "status": "claimed"})
                    logger.info(f"Playwright claimed {site['name']}")
                    page.close()
                except Exception as e:
                    msg = str(e)[:60]
                    results.append({"faucet": site["name"], "status": f"error: {msg}"})
                    logger.debug(f"Playwright error {site['name']}: {e}")
                time.sleep(3)
            browser.close()
        return results

def run():
    claimer = FaucetClaimer()
    return claimer.claim_all()
