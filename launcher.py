import os, sys, threading, time, logging, json
from pathlib import Path

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("noira1m.launcher")

CONFIG_PATH = BASE_DIR / "config" / "config.json"

def load_config() -> dict:
    default = {
        "agent": {"loop_interval_seconds": 30, "max_daily_trades": 50, "max_risk_per_trade_pct": 5,
                  "stop_loss_total_pct": 30, "min_balance_to_trade": 10},
        "modules": {"trading": {"enabled": True, "interval_minutes": 15},
                    "airdrops": {"enabled": True, "interval_minutes": 60},
                    "faucets": {"enabled": True, "interval_minutes": 30},
                    "freelance": {"enabled": False, "interval_minutes": 120}},
        "dashboard": {"host": "127.0.0.1", "port": 3001, "auto_open": True},
        "api_keys": {"gemini": "", "supabase_url": "", "supabase_key": "",
                     "bybit_api_key": "", "bybit_api_secret": "", "exchange": "bybit"}
    }
    try:
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH) as f:
                loaded = json.load(f)
                for k, v in loaded.items():
                    if isinstance(v, dict) and k in default:
                        default[k].update(v)
                    else:
                        default[k] = v
    except Exception as e:
        logger.warning(f"Config error: {e}")
    return default

def main():
    config = load_config()
    logger.info("Starting NOIRA1M Agent + Dashboard")

    from orchestrator import state, start as start_agent
    from dashboard.server import run as run_dashboard

    dash_config = config.get("dashboard", {})
    agent_thread = threading.Thread(target=start_agent, daemon=True, name="agent")
    agent_thread.start()

    time.sleep(2)
    run_dashboard(
        host=dash_config.get("host", "127.0.0.1"),
        port=dash_config.get("port", 3001),
        auto_open=dash_config.get("auto_open", True),
    )

if __name__ == "__main__":
    main()
