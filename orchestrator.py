import logging, json, time, sys
from datetime import datetime, timezone
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("noira1m")

BASE = Path(__file__).parent
DATA = BASE / "data"
DATA.mkdir(exist_ok=True)

def save(key, value):
    path = DATA / f"{key}.json"
    try:
        existing = json.loads(path.read_text())
    except:
        existing = []
    if isinstance(existing, list):
        if isinstance(value, list):
            existing = value + existing[:200]
        else:
            existing.insert(0, value)
            existing = existing[:200]
    path.write_text(json.dumps(existing, indent=2, default=str))

def append_log(msg):
    log_path = DATA / "log.txt"
    entry = f"[{datetime.now(timezone.utc).isoformat()}] {msg}"
    try:
        lines = log_path.read_text().splitlines()
    except:
        lines = []
    lines.insert(0, entry)
    log_path.write_text("\n".join(lines[:100]))
    logger.info(msg)

def run():
    append_log("Agent started")
    results = {}

    try:
        from sources.rss import scan as scan_rss
        rss = scan_rss()
        save("airdrops", rss)
        results["rss"] = len(rss)
        append_log(f"RSS: {len(rss)} airdrops found")
    except Exception as e:
        append_log(f"RSS error: {e}")

    try:
        from sources.twitter import scan as scan_twitter
        tw = scan_twitter()
        save("twitter", tw)
        results["twitter"] = len(tw)
        append_log(f"Twitter: {len(tw)} opportunities")
    except Exception as e:
        append_log(f"Twitter error: {e}")

    try:
        from sources.web import scan as scan_web
        web = scan_web()
        save("web", web)
        results["web"] = len(web)
        append_log(f"Web: {len(web)} opportunities")
    except Exception as e:
        append_log(f"Web error: {e}")

    try:
        from farming.faucets import run as claim_faucets
        faucet_results = claim_faucets()
        save("faucet_results", faucet_results)
        claimed = sum(1 for r in faucet_results if r.get("status") == "claimed")
        results["faucets_claimed"] = claimed
        append_log(f"Faucets: {claimed} claimed")
    except Exception as e:
        append_log(f"Faucet error: {e}")

    try:
        from farming.testnet import farm_all
        farm = farm_all()
        save("farming", farm)
        results["farming"] = farm
        append_log(f"Farming: {farm.get('tx_sent',0)} tx, {farm.get('wallets_created',0)} wallets")
    except Exception as e:
        append_log(f"Farming error: {e}")

    state = {"last_run": datetime.now(timezone.utc).isoformat(), "results": results}
    save("state", state)
    append_log(f"Agent done: {json.dumps(results)}")

if __name__ == "__main__":
    run()
