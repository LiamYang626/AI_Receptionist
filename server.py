# server.py
import asyncio
import threading
import time
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn

app = FastAPI()

app.mount("/Interface", StaticFiles(directory="Interface", html=True), name="static")

# Allow all origins (for local testing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connection manager to keep track of active WebSocket connections.
class ConnectionManager:
    def __init__(self):
        self.active_connections = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                print("Broadcast error:", e)


manager = ConnectionManager()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Optionally, handle messages from the client.
            data = await websocket.receive_text()
            await websocket.send_text(f"Server received: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)


def ui_queue_listener(ui_queue, loop):
    """Continuously poll the shared UI queue and broadcast messages to all WebSocket clients."""
    while True:
        if not ui_queue.empty():
            message = ui_queue.get()
            # Convert the structured message (a dict) to JSON.
            message_str = json.dumps(message)
            asyncio.run_coroutine_threadsafe(manager.broadcast(message_str), loop)
        time.sleep(0.1)


def run_server(ui_queue):
    # Get the current event loop from the main thread.
    loop = asyncio.get_event_loop()
    # Start the UI queue listener in a background thread.
    thread = threading.Thread(target=ui_queue_listener, args=(ui_queue, loop), daemon=True)
    thread.start()
    # Run the FastAPI server.
    uvicorn.run(app, host="127.0.0.1", port=5500)
