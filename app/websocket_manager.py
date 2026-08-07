from typing import Dict, Set

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.players: Dict[str, Set[WebSocket]] = {}
        self.spectators: Dict[str, Set[WebSocket]] = {}

    async def connect(
        self, game_id: str, websocket: WebSocket, role: str = "spectator"
    ):
        await websocket.accept()
        if role == "player":
            self.players.setdefault(game_id, set()).add(websocket)
        else:
            self.spectators.setdefault(game_id, set()).add(websocket)

    def disconnect(self, game_id: str, websocket: WebSocket, role: str = "spectator"):
        target_map = self.players if role == "player" else self.spectators
        if game_id in target_map:
            target_map[game_id].discard(websocket)
            if not target_map[game_id]:
                del target_map[game_id]

    async def broadcast_to_room(self, game_id: str, message: dict):
        """
        Sends updates to ALL connected clients
        """
        all_connections = self.players.get(game_id, set()).union(
            self.spectators.get(game_id, set())
        )

        for connection in list(all_connections):
            try:
                await connection.send_json(message)
            except Exception:
                pass


manager = ConnectionManager()
