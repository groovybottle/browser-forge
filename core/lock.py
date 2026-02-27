import asyncio

_locks: dict[str, asyncio.Lock] = {}


def get_lock(provider: str) -> asyncio.Lock:
    if provider not in _locks:
        _locks[provider] = asyncio.Lock()
    return _locks[provider]
