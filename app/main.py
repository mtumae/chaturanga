
import os
import uuid
from typing import Dict

import chess
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket
from google import genai
from pydantic.main import BaseModel
from starlette.exceptions import HTTPException
from starlette.websockets import WebSocketDisconnect
from websocket_manager import manager

load_dotenv()
app = FastAPI(title="chaturanga")
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


game_boards: Dict[str, chess.Board] = {}


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

                ai_move_uci, commentary = await generate_gemini_move(board.fen())
                board.push(chess.Move.from_uci(ai_move_uci))

                await manager.broadcast_to_room(
                    game_id,
                    {
                        "event": "ai_moved",
                        "fen": board.fen(),
                        "last_move": ai_move_uci,
                        "commentary": commentary,
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


async def generate_gemini_move(fen_string: str):
    """Asynchronously calls Gemini to retrieve a valid move and commentary."""
    print("Model is thinking...")

    # optimized_prompt should look something like:
    # FEN: rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1
    # Legal moves: [e7e5, c7c5, e7e6, g8f6]
    # Task: Return JSON with "move" (from legal moves) and "commentary" (max 15 words).
    prompt = f"""
        You are playing a chess game.
        Current Board Position (FEN): {fen_string}

        Task: Respond with JSON only containing:
        1. "move": Your next move in UCI notation (e.g., "g1f3", "e7e5").
        2. "commentary": A short sentence strategic remark.
        """

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents={"text": prompt},
        config={
            "response_mime_type": "application/json",
            "temperature": 0.2,
            "max_output_tokens": 80,
        },
    )

    if response.text:
        import json
        result = json.loads(response.text)
        print(result)
        return result["move"], result["commentary"]
    else:
        return None
