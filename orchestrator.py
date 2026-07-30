import os, sys, json, time, logging
from datetime import datetime, timezone
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("noira1m")

BASE = Path(__file__).parent
DATA = BASE / "data"
DATA.mkdir(exist_ok=True)

def log(msg):
    logger.info(msg)
    (DATA / "last_log.txt").write_text(f"[{datetime.now(timezone.utc).isoformat()}] {msg}")

def load_state() -> dict:
    try:
        return json.loads((DATA / "state.json").read_text())
    except:
        return {"total_claims": 0, "total_found": 0, "runs": 0, "errors": []}

def save_state(s):
    (DATA / "state.json").write_text(json.dumps(s, indent=2))

def run_agent():
    state = load_state()
    state["runs"] += 1
    state["last_run"] = datetime.now(timezone.utc).isoformat()

    from modules.airdrops import fetch_airdrops

    log("NOIRA1M agent started")

    airdrops = fetch_airdrops()
    if airdrops:
        state["total_found"] += len(airdrops)
        found_path = DATA / "found_airdrops.json"
        try:
            existing = json.loads(found_path.read_text())
        except:
            existing = []
        for a in airdrops:
            a["found_at"] = datetime.now(timezone.utc).isoformat()
            existing.append(a)
        # Keep last 500
        existing = existing[-500:]
        found_path.write_text(json.dumps(existing, indent=2))
        log(f"Found {len(airdrops)} airdrops")

    from modules.faucets import FaucetManager
    fm = FaucetManager(str(DATA))
    results = fm.claim_all()
    claimed = sum(1 for r in results if r.get("status") == "claimed")
    if claimed:
        state["total_claims"] += claimed
        log(f"Claimed {claimed} faucets")

    log(f"Agent done. Total airdrops: {state['total_found']}, faucets: {state['total_claims']}")
    save_state(state)

if __name__ == "__main__":
    run_agent()
