import os, sys, json, time, logging, threading
from datetime import datetime, timezone
from pathlib import Path
from modules.trading import find_opportunities
from modules.airdrops import fetch_airdrops, scan_twitter_airdrops
from modules.faucets import FaucetManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s %(message)s")
logger = logging.getLogger("noira1m")

BASE_DIR = Path(__file__).parent
CONFIG_PATH = BASE_DIR / "config" / "config.json"
DATA_DIR = BASE_DIR / "data"

class AgentState:
    def __init__(self):
        self.balance = 0.0
        self.total_trades = 0
        self.wins = 0
        self.losses = 0
        self.signals = []
        self.airdrops = []
        self.faucet_results = []
        self.errors = []
        self.running = True
        self._lock = threading.Lock()

    def to_dict(self):
        with self._lock:
            return {
                "balance": round(self.balance, 2),
                "total_trades": self.total_trades,
                "wins": self.wins,
                "losses": self.losses,
                "win_rate": f"{round(self.wins/(self.wins+self.losses)*100,1)}%" if self.wins+self.losses > 0 else "0%",
                "signals_last_hour": len([s for s in self.signals if (datetime.now(timezone.utc) - datetime.fromisoformat(s.get("time","2000-01-01"))).total_seconds() < 3600]),
                "airdrops_found": len(self.airdrops),
                "faucets_claimed": len([f for f in self.faucet_results if f.get("status") == "claimed"]),
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "running": self.running,
            }

    def add_signal(self, signal: dict):
        with self._lock:
            signal["time"] = datetime.now(timezone.utc).isoformat()
            self.signals.insert(0, signal)
            self.signals = self.signals[:200]
            self.total_trades += 1

    def add_error(self, error: str):
        with self._lock:
            self.errors.insert(0, {"time": datetime.now(timezone.utc).isoformat(), "msg": error})
            self.errors = self.errors[:50]

state = AgentState()

def trading_loop():
    while state.running:
        try:
            ops = find_opportunities()
            for op in ops:
                state.add_signal(op)
            if ops:
                logger.info(f"Trading: {len(ops)} opportunities found")
        except Exception as e:
            state.add_error(str(e))
            logger.error(f"Trading error: {e}")
        for _ in range(60):
            if not state.running:
                return
            time.sleep(15)

def airdrop_loop():
    while state.running:
        try:
            ads = fetch_airdrops()
            if ads:
                state.airdrops = ads + state.airdrops[:50]
                logger.info(f"Airdrops: {len(ads)} new found")
        except Exception as e:
            state.add_error(f"Airdrop: {str(e)[:50]}")
        for _ in range(120):
            if not state.running:
                return
            time.sleep(30)

def faucet_loop():
    fm = FaucetManager(str(DATA_DIR))
    while state.running:
        try:
            results = fm.claim_all()
            state.faucet_results = results + state.faucet_results[:50]
            claimed = sum(1 for r in results if r.get("status") == "claimed")
            if claimed:
                logger.info(f"Faucets: {claimed} claimed")
        except Exception as e:
            state.add_error(f"Faucet: {str(e)[:50]}")
        for _ in range(60):
            if not state.running:
                return
            time.sleep(60)

def start():
    logger.info("=" * 50)
    logger.info("NOIRA1M Agent v1.0 Starting")
    logger.info("=" * 50)

    threads = [
        threading.Thread(target=trading_loop, daemon=True, name="trading"),
        threading.Thread(target=airdrop_loop, daemon=True, name="airdrops"),
        threading.Thread(target=faucet_loop, daemon=True, name="faucets"),
    ]
    for t in threads:
        t.start()
        time.sleep(0.5)

    logger.info("All modules started")
    try:
        while state.running:
            time.sleep(5)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        state.running = False

if __name__ == "__main__":
    start()
