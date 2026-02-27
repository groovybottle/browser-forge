import os
import time
from datetime import datetime

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel

from config import OUTPUT_ROOT
from core.lock import get_lock
from providers.gemini_nano import GeminiNanoProvider

router = APIRouter()

PROVIDERS = {
    "gemini_nano": GeminiNanoProvider(),
}


class GenerateRequest(BaseModel):
    prompt: str
    filename: str = "image"
    provider: str = "gemini_nano"


@router.post("/generate")
async def generate_image(req: GenerateRequest):
    if req.provider not in PROVIDERS:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {req.provider}")

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
            success = await provider.generate(req.prompt, output_path)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    if not success or not os.path.exists(output_path):
        raise HTTPException(status_code=500, detail="Image generation failed")

    with open(output_path, "rb") as f:
        image_data = f.read()

    return Response(content=image_data, media_type="image/png")
