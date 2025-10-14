from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import json, time, threading
from typing import List, Generator

from .event_router import route_frontend_ping
from main.utils.status import status_manager

lock = threading.Lock()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConnectionManager:
    def __init__(self, test: bool = False) -> None:
        self.current_connection: WebSocket | None = None
        self.test = test

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()

        if self.current_connection is not None:
            print('Kicking old client off for new client')

        self.current_connection = websocket

        await self.ping()

    def disconnect(self, websocket: WebSocket) -> None:
        self.current_connection = None
        print('Websocket disconnected')

    async def artifact_detected(self, data: List[List[float]]) -> None:

        if self.current_connection is None:
            print('Tried to return but no websocket active', 'artifact_detected')
            return

        await self.current_connection.send_json({
            'type': 'artifact_detected',
            'data': {'eeg_data': data},
        })

    async def ping(self) -> None:

        if self.current_connection is None:
            print('Tried to return but no websocket active', 'ping')
            return

        await self.current_connection.send_json({
            'type': 'ping',
            'data': {},
        })

manager = ConnectionManager()

@app.get('/status-updates')
async def status_update() -> StreamingResponse:
    
    def status_generator() -> Generator[str, None, None]:
        
        last_value: str = 'not connected'
        
        yield f"data: {json.dumps({'status': last_value})}\n\n"
        
        while True:
            
            with lock:
                if last_value != status_manager.status:
                    last_value = status_manager.status
                    # Format for SSE
                    yield f"data: {json.dumps({'status': last_value})}\n\n"
                
            time.sleep(0.1)

    return StreamingResponse(status_generator(), media_type="text/event-stream")

@app.websocket("/event_manager")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    
    # Send initial connection message
    await manager.ping()
    
    try:
        while True:
            # Receive messages from client (optional)
            data = await websocket.receive_text()
            message = json.loads(data)
            print(f"Received from client: {message}")

            await route_frontend_ping(message, manager)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"Error: {e}")
        manager.disconnect(websocket)

# HTTP endpoint to check server status
@app.get("/")
async def root():
    return {'message': 'Use the Force, Luke. Let go.'}