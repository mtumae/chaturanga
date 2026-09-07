from google import genai
from dotenv import load_dotenv
import os

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

async def generate_move(fen_string: str):
    """Asynchronously calls Gemini to retrieve a valid move and commentary."""

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
        3. "expression": Pick one of the expressions "Laughing", "Worried", "Angry", or "Skeptical" to go along with your thought process.
        """

    response = client.models.generate_content(
        model="gemini-3.1-flash-lite",
        contents={"text": prompt},
        config={
            "response_mime_type": "application/json",
            "temperature": 0.2,
        },
    )

    if response.text:
        import json
        result = json.loads(response.text)
        return {
            'ai_move_uci': result['move'],
            'commentary': result['commentary'],
            'expression': result['expression'],
        }
