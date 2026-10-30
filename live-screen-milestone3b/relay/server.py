"""Development-only authenticated JPEG relay. Run on a trusted local network only."""
from __future__ import annotations
import asyncio
import hmac
import os
import time
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI(title="WorkforceOS Native Screen Relay (dev)")
SEND_TOKEN = os.getenv("WFOS_SEND_TOKEN", "")
VIEW_TOKEN = os.getenv("WFOS_VIEW_TOKEN", "")
DEVICE_ID = os.getenv("WFOS_DEVICE_ID", "")
MAX_FRAME = 900_000
LAST_FRAME = None
LAST_AT = 0.0
CONNECTIONS: set[WebSocket] = set()
SENDER: WebSocket | None = None

def verify(received: str, secret: str) -> bool:
    return len(secret) >= 32 and hmac.compare_digest(received, secret)

@app.get('/health')
def health():
    return {'relay': 'running', 'sender_connected': SENDER is not None, 'viewers':len(CONNECTIONS), 'frame_fresh': time.monotonic() - LAST_AT < 4}

@app.websocket('/ws/send/{device_id}')
async def send(ws: WebSocket, device_id: str):
    global SENDER, LAST_FRAME, LAST_AT
    if device_id != DEVICE_ID or not verify(ws.query_params.get('token',''), SEND_TOKEN) or SENDER is not None:
        await ws.close(code=1008)
        return
    await ws.accept()
    SENDER = ws
    try:
        while True:
            data = await ws.receive_bytes()
            if len(data) < 32 or len(data) > MAX_FRAME or not data.startswith(b'\xff\xd8') or not data.endswith(b'\xff\xd9'):
                await ws.close(code=1009)
                return
            LAST_FRAME, LAST_AT = data, time.monotonic()
            stale = []
            for viewer in tuple(CONNECTIONS):
                try:
                    await asyncio.wait_for(viewer.send_bytes(data), timeout=0.4)
                except Exception:
                    stale.append(viewer)
            for viewer in stale:
                CONNECTIONS.discard(viewer)
                try: await viewer.close()
                except Exception: pass
    except (WebSocketDisconnect, RuntimeError):
        pass
    finally:
        if SENDER is ws:
            SENDER = None
            LAST_FRAME, LAST_AT = None, 0.0
            for viewer in tuple(CONNECTIONS):
                try: await viewer.send_text('stopped')
                except Exception: pass

@app.websocket('/ws/view/{device_id}')
async def view(ws: WebSocket, device_id: str):
    if device_id != DEVICE_ID or not verify(ws.query_params.get('token',''), VIEW_TOKEN):
        await ws.close(code=1008)
        return
    await ws.accept()
    CONNECTIONS.add(ws)
    try:
        if LAST_FRAME is not None and time.monotonic() - LAST_AT < 4:
            await ws.send_bytes(LAST_FRAME)
        while True:
            await ws.receive_text()
    except (WebSocketDisconnect, RuntimeError):
        pass
    finally:
        CONNECTIONS.discard(ws)
