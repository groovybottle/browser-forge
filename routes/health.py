import urllib.request
from datetime import datetime

from fastapi import APIRouter

from config import CDP_HOST, CDP_PORT
from routes.image import PROVIDERS

router = APIRouter()


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
        "version": "1.1.0",
        "time": datetime.now().isoformat(),
        "cdp": {
            "connected": _cdp_connected(),
            "port": CDP_PORT,
        },
        "providers": {
            name: provider.check_tab()
            for name, provider in PROVIDERS.items()
        },
    }
