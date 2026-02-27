import os

import uvicorn
from fastapi import FastAPI

from config import OUTPUT_ROOT, SERVER_PORT
from routes.health import router as health_router
from routes.image import router as image_router

app = FastAPI(title="browser-forge", version="1.0.0")

app.include_router(image_router, prefix="/api/v1/image")
app.include_router(health_router)


@app.on_event("startup")
async def startup_event():
    os.makedirs(OUTPUT_ROOT, exist_ok=True)
    print(f"browser-forge v1.0 started | output: {os.path.abspath(OUTPUT_ROOT)}")


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=SERVER_PORT)
