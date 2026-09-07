
from contextlib import asynccontextmanager
from multiprocessing import Value
import os
import uuid
from typing import Dict

import chess
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, Depends
from pydantic.main import BaseModel
from starlette.exceptions import HTTPException
from starlette.websockets import WebSocketDisconnect
from app.websocket_manager import ConnectionManager
from app.services.ai_engine import generate_move
from sqlmodel import Session, create_engine

load_dotenv()
app = FastAPI(title="chaturanga")
engine = create_engine("sqlite:///database.db")
manager = ConnectionManager()

game_boards: Dict[str, chess.Board] = {}
@asynccontextmanager
async def lifespan(app: FastAPI):
    with Session(engine) as session:
        yield session


class CreateGameRequest(BaseModel):
    user_id: str
    player_color: str = "black"


@app.get("/")
def read_root():
    return {"status": "online", "message": "FastAPI is running."}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.post("/games/create")
async def create_game(req: CreateGameRequest):
    game_id = str(uuid.uuid4())
    board = chess.Board()
    game_boards[game_id] = board

    return {
        "game_id": game_id,
        "fen": board.fen(),
        "player_color": req.player_color,
        "status": "active",
    }


@app.get("/games/{game_id}")
async def get_game(game_id: str):
    if game_id not in game_boards:
        raise HTTPException(status_code=404, detail="Game not found")
    board = game_boards[game_id]
    return {
        "game_id": game_id,
        "fen": board.fen(),
        "is_game_over": board.is_game_over(),
    }


@app.websocket("/ws/chess/{game_id}")
async def chess_ws(websocket: WebSocket, game_id: str, role: str = "spectator"):
    await manager.connect(game_id, websocket, role=role)
    board = game_boards.setdefault(game_id, chess.Board())
    await websocket.send_json(
        {
            "event": "initial_state",
            "fen": board.fen(),
            "role": role,
            "spectator_count": len(manager.spectators.get(game_id, set())),
        }
    )

    try:
        while True:
            data = await websocket.receive_json()
            if role == "spectator":
                await websocket.send_json(
                    {"error": "Permission denied. You are a spectator NOT a player."}
                )
                continue

            action = data.get("action")
            if action == "move":
                user_move_uci = data.get("move")
                try:
                    move = chess.Move.from_uci(user_move_uci)
                    if move not in board.legal_moves:
                        await websocket.send_json(
                            {"error": "Illegal move", "fen": board.fen()}
                        )
                        continue
                    board.push(move)
                except ValueError:
                    await websocket.send_json({"error": "Invalid UCI move string"})
                    continue

                await manager.broadcast_to_room(
                    game_id,
                    {
                        "event": "user_moved",
                        "fen": board.fen(),
                        "last_move": user_move_uci,
                    },
                )

                if board.is_game_over():
                    await manager.broadcast_to_room(
                        game_id, {"event": "game_over", "result": board.result()}
                    )
                    break

                try:
                    move = await generate_move(board.fen())
                except Exception as e:
                    await websocket.send_json({"error": str(e)})
                    continue
                if move:
                    ai_move_uci, commentary, expression = move['ai_move_uci'], move['commentary'], move['expression']
                    print(f"Expression: {expression}")
                    board.push(chess.Move.from_uci(ai_move_uci))
                    await manager.broadcast_to_room(
                        game_id,
                        {
                            "event": "ai_moved",
                            "fen": board.fen(),
                            "last_move": ai_move_uci,
                            "commentary": commentary,
                            "expression": expression,
                        },
                    )
                else:
                    await manager.broadcast_to_room(
                        game_id,
                        {
                            "event": "ai_moved",
                            "fen": board.fen(),
                            "last_move": None,
                            "commentary": "Move not found",
                            "expression": None,
                        },
                    )

    except WebSocketDisconnect:
        manager.disconnect(game_id, websocket, role=role)
        await manager.broadcast_to_room(
            game_id,
            {
                "event": "presence_update",
                "spectator_count": len(manager.spectators.get(game_id, set())),
            },
        )
