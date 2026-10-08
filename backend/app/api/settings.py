from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.models.user import User
from app.api.deps import get_current_user

router = APIRouter(prefix="/settings", tags=["Application & AI Mode Settings"])


class AIModeUpdateRequest(BaseModel):
    mode: str = Field(..., description="One of: 'offline', 'hybrid', 'online'")
    local_model_name: Optional[str] = "fastembed-bge-small-en-v1.5"
    cloud_fallback_enabled: Optional[bool] = False


class AIModeResponse(BaseModel):
    mode: str
    label: str
    description: str
    status_indicator: str
    local_model_name: str
    cloud_fallback_enabled: bool


# Default mode settings per user
_user_ai_modes: Dict[str, Dict[str, Any]] = {}

MODE_METADATA = {
    "offline": {
        "label": "Offline AI",
        "description": "No Internet required. Full on-device reasoning and local embeddings.",
        "status_indicator": "🟢 Offline AI — No Internet required",
    },
    "hybrid": {
        "label": "Hybrid AI",
        "description": "Local data indexing with cloud reasoning for complex explanations.",
        "status_indicator": "🟡 Hybrid — Local data + cloud reasoning",
    },
    "online": {
        "label": "Online AI",
        "description": "Cloud AI enabled with highest capability frontier reasoning.",
        "status_indicator": "🔵 Online — Cloud AI enabled",
    },
}


@router.get("/ai-mode", response_model=AIModeResponse)
async def get_ai_mode(current_user: User = Depends(get_current_user)):
    """Retrieve the current user's AI operation mode."""
    config = _user_ai_modes.get(
        current_user.id,
        {
            "mode": "offline",
            "local_model_name": "fastembed-bge-small-en-v1.5",
            "cloud_fallback_enabled": False,
        },
    )
    mode = config["mode"]
    meta = MODE_METADATA.get(mode, MODE_METADATA["offline"])
    return AIModeResponse(
        mode=mode,
        label=meta["label"],
        description=meta["description"],
        status_indicator=meta["status_indicator"],
        local_model_name=config.get("local_model_name", "fastembed-bge-small-en-v1.5"),
        cloud_fallback_enabled=config.get("cloud_fallback_enabled", False),
    )


@router.post("/ai-mode", response_model=AIModeResponse)
async def set_ai_mode(
    req: AIModeUpdateRequest,
    current_user: User = Depends(get_current_user),
):
    """Set the user's AI operation mode (offline, hybrid, online)."""
    norm_mode = req.mode.lower().strip()
    if norm_mode not in MODE_METADATA:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid AI mode '{req.mode}'. Allowed modes: {list(MODE_METADATA.keys())}",
        )

    _user_ai_modes[current_user.id] = {
        "mode": norm_mode,
        "local_model_name": req.local_model_name or "fastembed-bge-small-en-v1.5",
        "cloud_fallback_enabled": req.cloud_fallback_enabled or False,
    }

    meta = MODE_METADATA[norm_mode]
    return AIModeResponse(
        mode=norm_mode,
        label=meta["label"],
        description=meta["description"],
        status_indicator=meta["status_indicator"],
        local_model_name=req.local_model_name or "fastembed-bge-small-en-v1.5",
        cloud_fallback_enabled=req.cloud_fallback_enabled or False,
    )
