# browser-forge

Personal automation server that controls a logged-in browser via CDP (Chrome DevTools Protocol) to provide AI services as an API. Currently supports Gemini Nano Banana Pro for image generation.

No API keys needed — uses browser sessions directly.

## Requirements

- Python 3.10+
- Google Chrome launched with `--remote-debugging-port=18800`
- Gemini account logged in at `gemini.google.com`

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
# Start the server
./start.sh
# or
python server.py
```

### Generate an image

```bash
curl -X POST http://127.0.0.1:19922/api/v1/image/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "A futuristic cityscape at sunset"}' \
  --output image.png
```

### Health check

```bash
curl http://127.0.0.1:19922/health
```

## Cross-platform

Works on macOS and Linux. No OS-specific dependencies (no clipboard, no peekaboo, no osascript). Pure Python + CDP WebSocket only.
