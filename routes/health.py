import json
import urllib.request
from datetime import datetime

from fastapi import APIRouter

from config import CDP_HOST, CDP_PORT
from providers.gemini_nano import GeminiNanoProvider

router = APIRouter()

_gemini = GeminiNanoProvider()


def _cdp_connected() -> bool:
    try:
        with urllib.request.urlopen(f"http://{CDP_HOST}:{CDP_PORT}/json/version", timeout=3) as resp:
            return resp.status == 200
    except Exception:
        return False


@router.get("/health")
def health():
    return {
        "status": "ok",
        "server": "browser-forge",
        "version": "1.0.0",
        "time": datetime.now().isoformat(),
        "cdp": {
            "connected": _cdp_connected(),
            "port": CDP_PORT,
        },
        "providers": {
            "gemini_nano": _gemini.check_tab(),
        },
    }
