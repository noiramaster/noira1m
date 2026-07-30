import json, webbrowser, logging
from pathlib import Path
from datetime import datetime, timezone
import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

logger = logging.getLogger("noira1m.dashboard")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

BASE = Path(__file__).parent.parent
DATA = BASE / "data"

app = FastAPI(title="NOIRA1M Dashboard")

@app.get("/")
async def index():
    html = (Path(__file__).parent / "index.html").read_text(encoding="utf-8")
    return HTMLResponse(html)

@app.get("/api/state")
async def get_state():
    try:
        s = json.loads((DATA / "state.json").read_text())
        return s
    except:
        return {"runs": 0, "total_claims": 0, "total_found": 0, "errors": []}

@app.get("/api/airdrops")
async def get_airdrops():
    try:
        ads = json.loads((DATA / "found_airdrops.json").read_text())
        return ads[-20:]
    except:
        return []

@app.get("/api/faucets")
async def get_faucets():
    try:
        ads = json.loads((DATA / "faucet_claims.json").read_text())
        return ads
    except:
        return {}

@app.get("/api/logs")
async def get_logs():
    try:
        return (DATA / "last_log.txt").read_text()
    except:
        return "No logs yet"

def run(host="127.0.0.1", port=3001, auto_open=True):
    if auto_open:
        webbrowser.open(f"http://{host}:{port}")
    logger.info(f"Dashboard: http://{host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")

if __name__ == "__main__":
    run()
