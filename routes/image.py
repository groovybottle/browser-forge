import os
import time
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel

from config import OUTPUT_ROOT
from core.lock import get_lock
from providers.gemini_nano import GeminiNanoProvider
from providers.nano_banana import NanoBananaProvider

router = APIRouter()

PROVIDERS = {
    "gemini_nano": GeminiNanoProvider(),
    "nano_banana": NanoBananaProvider(),
}


class GenerateRequest(BaseModel):
    prompt: str
    filename: str = "image"
    provider: str = "gemini_nano"
    # nano_banana extras
    input_images: Optional[list[str]] = None   # local paths for editing
    aspect_ratio: Optional[str] = "1:1"        # 1:1, 9:16, 16:9, etc.
    resolution: Optional[str] = "2K"           # 1K, 2K, 4K


@router.post("/generate")
async def generate_image(req: GenerateRequest):
    if req.provider not in PROVIDERS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown provider: {req.provider}. Available: {list(PROVIDERS.keys())}",
        )

    provider = PROVIDERS[req.provider]
    lock = get_lock(req.provider)

    # Date folder: output/YYYY-MM-DD/
    today_str = datetime.now().strftime("%Y-%m-%d")
    save_dir = os.path.join(OUTPUT_ROOT, today_str)
    os.makedirs(save_dir, exist_ok=True)

    # Filename: TIMESTAMP_filename.png
    timestamp = int(time.time())
    safe_name = "".join(c for c in req.filename if c.isalnum() or c in ("-", "_")).rstrip()
    if not safe_name:
        safe_name = "image"
    output_path = os.path.join(save_dir, f"{timestamp}_{safe_name}.png")

    async with lock:
        try:
            # Pass extra kwargs for nano_banana
            if req.provider == "nano_banana":
                success = await provider.generate(
                    req.prompt,
                    output_path,
                    input_images=req.input_images,
                    aspect_ratio=req.aspect_ratio or "1:1",
                    resolution=req.resolution or "2K",
                )
            else:
                success = await provider.generate(req.prompt, output_path)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    if not success or not os.path.exists(output_path):
        raise HTTPException(status_code=500, detail="Image generation failed")

    with open(output_path, "rb") as f:
        image_data = f.read()

    # Detect image format by magic bytes
    media_type = "image/png"
    if image_data[:3] == b"\xff\xd8\xff":
        media_type = "image/jpeg"
    elif image_data[:4] == b"\x89PNG":
        media_type = "image/png"
    elif image_data[:4] == b"RIFF" and image_data[8:12] == b"WEBP":
        media_type = "image/webp"

    return Response(content=image_data, media_type=media_type)
