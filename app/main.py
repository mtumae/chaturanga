import os
import uuid
from typing import Dict, List, Optional, Literal
from pydantic import AliasChoices, Field

import chess
from dotenv import load_dotenv
from datetime import datetime
from fastapi import Depends, FastAPI, WebSocket
from pydantic.main import BaseModel
from starlette.exceptions import HTTPException
from starlette.websockets import WebSocketDisconnect
from app.websocket_manager import ConnectionManager
from app.crud.game import save_game, get_all_games
from app.crud.player import PlayerRatingRequest
from app.crud.player import update_player_rating
from app.services.ai_engine import AIServiceError, generate_move
from services.db import check_database_connection, get_session
from sqlmodel import Session
from contextlib import asynccontextmanager


load_dotenv()

manager = ConnectionManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Initializing database...")
    check_database_connection()
    print("Database connection OK")
    yield


app = FastAPI(title="chaturanga", lifespan=lifespan)


game_boards: Dict[str, chess.Board] = {}


class CreateGameRequest(BaseModel):
    user_id: str
    player_color: str = "black"


class PaginatedGamesRequest(BaseModel):
    page: int
    offset: int
    limit: int


class SaveGameRequest(BaseModel):
    game_id: str = Field(validation_alias=AliasChoices("gameId", "game_id"))
    player_id: str = Field(validation_alias=AliasChoices("playerId", "player_id"))
    fen: str
    bot_tier: int = Field(validation_alias=AliasChoices("botTier", "bot_tier"))
    outcome: Literal["w", "l", "d"]
    moves_history: List[str] = Field(
        validation_alias=AliasChoices("movesHistory", "moves_history")
    )
    pgn: str
    updated_at: datetime = Field(
        validation_alias=AliasChoices("updatedAt", "updated_at")
    )
    winner_id: str | None = Field(
        validation_alias=AliasChoices("winnerId", "winner_id")
    )
    status: Literal["completed", "pending", "abandoned"]


@app.get("/")
def read_root():
    return {"status": "online", "message": "FastAPI is running."}


@app.post("/games/save")
async def save_new_game(
    request: SaveGameRequest, db_session: Session = Depends(get_session)
):
    try:
        save_game(
            session=db_session,
            game_id=request.game_id,
            player_id=request.player_id,
            fen=request.fen,
            moves_history=request.moves_history,
            pgn=request.pgn,
            status=request.status,
        )
        if request.status == "completed":
            update_player_rating(
                session=db_session,
                player_id=request.player_id,
                bot_tier=request.bot_tier,
                outcome=request.outcome,
            )
    except Exception as e:
        print(f"[save_new_game]: Failed to save game {str(e)}")
        raise HTTPException(500, "Failed to save game.")

    return {"success": True, "message": "Game saved successfully."}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


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


@app.get("/games/all")
async def get_paginated_games(
    request: PaginatedGamesRequest, db_session=Depends(get_session)
):
    try:
        get_all_games(session=db_session, limit=request.limit, offset=request.offset)
    except Exception as e:
        print(f"[save_new_game]: Failed to save game {str(e)}")
        raise HTTPException(500, "Failed to save game.")


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
                    ai_move_uci = move["ai_move_uci"]
                    commentary = move["commentary"]
                    expression = move["expression"]
                    try:
                        ai_move = chess.Move.from_uci(ai_move_uci)
                    except (TypeError, ValueError) as exc:
                        raise AIServiceError(
                            "AI service returned an invalid move.", 502
                        ) from exc
                    if ai_move not in board.legal_moves:
                        raise AIServiceError(
                            "AI service returned an illegal move.", 502
                        )
                    board.push(ai_move)
                except AIServiceError as exc:
                    await websocket.send_json(
                        {
                            "error": exc.message,
                            "status_code": exc.status_code,
                        }
                    )
                    continue

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

    except WebSocketDisconnect:
        manager.disconnect(game_id, websocket, role=role)
        await manager.broadcast_to_room(
            game_id,
            {
                "event": "presence_update",
                "spectator_count": len(manager.spectators.get(game_id, set())),
            },
        )
