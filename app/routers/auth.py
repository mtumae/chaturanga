from typing import Annotated

from clerk_backend_api.security.types import RequestState
from fastapi import APIRouter, Depends

from app.auth import require_auth

router = APIRouter(prefix="/api", tags=["protected"])

@router.get("/me")
def me(state: Annotated[RequestState, Depends(require_auth)]):
    assert state.payload is not None  # guaranteed by require_auth
    return {
        "user_id": state.payload["sub"],
        "session_id": state.payload.get("sid"),
    }
