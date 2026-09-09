from google import genai
from dotenv import load_dotenv
import json
import os

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


class AIServiceError(Exception):
    """An error returned when the upstream AI service cannot provide a move."""

    def __init__(self, message: str, status_code: int = 503):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


async def generate_move(fen_string: str):
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
        3. "expression": Select an expression to return with your move from : "Waiting", "Laughing", "Pissed", "Skeptical", "Worried".
        """

    try:
        response = client.models.generate_content(
            model="gemini-3.1-flash-lite",
            contents={"text": prompt},
            config={
                "response_mime_type": "application/json",
                "temperature": 0.2,
            },
        )

        if not response.text:
            raise AIServiceError("AI service returned an empty response.")

        result = json.loads(response.text)
        ai_move_uci = result["move"]
        commentary = result["commentary"]
        expression = result["expression"]
    except AIServiceError:
        raise
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        raise AIServiceError("AI service returned an invalid move.", 502) from exc
    except Exception as exc:
        raise AIServiceError("AI service is currently unavailable.", 503) from exc

    return {
        "ai_move_uci": ai_move_uci,
        "commentary": commentary,
        "expression": expression,
    }
