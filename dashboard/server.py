import os, sys, json, asyncio, webbrowser, logging
from pathlib import Path
from datetime import datetime, timezone
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles

BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))
from orchestrator import state

logger = logging.getLogger("noira1m.dashboard")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

app = FastAPI(title="NOIRA1M Dashboard")

@app.get("/")
async def get_dashboard():
    index_path = Path(__file__).parent / "index.html"
    if index_path.exists():
        return HTMLResponse(index_path.read_text(encoding="utf-8"))
    return {"status": "ok"}

@app.get("/api/state")
async def get_state():
    return state.to_dict()

@app.get("/api/signals")
async def get_signals():
    return state.signals[:50]

@app.get("/api/airdrops")
async def get_airdrops():
    return state.airdrops[:20]

@app.get("/api/errors")
async def get_errors():
    return state.errors[-20:]

connected_clients = set()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        connected_clients.discard(websocket)

async def broadcast():
    while True:
        if connected_clients:
            data = json.dumps(state.to_dict(), default=str)
            dead = set()
            for ws in connected_clients:
                try:
                    await ws.send_text(data)
                except Exception:
                    dead.add(ws)
            connected_clients -= dead
        await asyncio.sleep(2)

@app.on_event("startup")
async def startup():
    asyncio.create_task(broadcast())

def run(host: str = "127.0.0.1", port: int = 3001, auto_open: bool = True):
    url = f"http://{host}:{port}"
    if auto_open:
        webbrowser.open(url)
    logger.info(f"Dashboard: {url}")
    uvicorn.run(app, host=host, port=port, log_level="info")

if __name__ == "__main__":
    run()
