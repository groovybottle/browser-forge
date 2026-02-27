# browser-forge API Documentation

> CDP-based AI service automation server. Provides API access to browser-controlled AI services (Gemini Nano Banana Pro, etc.) without API keys.

**Version:** 1.0.0  
**Base URL:** `http://127.0.0.1:19922`  
**Status:** Active Development

---

## Quick Start

### Prerequisites

- macOS or Linux
- Python 3.10+
- Chrome running with `--remote-debugging-port=18800`
- Logged into Gemini (gemini.google.com/app)

### Setup

```bash
git clone https://github.com/groovybottle/browser-forge.git
cd browser-forge
chmod +x start.sh
./start.sh
```

### Test

```bash
# Health check
curl http://127.0.0.1:19922/health

# Generate image
curl -X POST http://127.0.0.1:19922/api/v1/image/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt":"A vibrant esports arena with neon lights"}' \
  --output image.png
```

---

## Endpoints

### `POST /api/v1/image/generate`

Generate an image using Gemini Nano Banana Pro via browser automation.

**Request Body** (JSON):
```json
{
  "prompt": "string (required)",
  "filename": "string (optional, default: 'image')",
  "provider": "string (optional, default: 'gemini_nano')"
}
```

**Parameters:**

| Name | Type | Required | Description | Example |
|------|------|----------|-------------|---------|
| `prompt` | string | ✅ | Image generation prompt (Korean or English) | `"광활한 스포츠 스타디움, 밝은 조명"` |
| `filename` | string | ❌ | Output filename (alphanumeric + `-_`) | `"t1_esports_arena"` |
| `provider` | string | ❌ | AI service provider name | `"gemini_nano"` |

**Response:**

- **Success (200):** PNG image binary
  ```
  Content-Type: image/png
  Content-Length: <file-size>
  ```

- **Error (400):** Bad Request
  ```json
  {"detail": "prompt cannot be empty"}
  ```

- **Error (500):** Server Error
  ```json
  {"detail": "Failed to generate AI image 1 after retry: ..."}
  ```

**Examples:**

**Basic:**
```bash
curl -X POST http://127.0.0.1:19922/api/v1/image/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt":"A trophy on a stadium stage"}' \
  --output trophy.png
```

**With Custom Filename:**
```bash
curl -X POST http://127.0.0.1:19922/api/v1/image/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt":"League of Legends champions battling in an arena",
    "filename":"lol_battle_2026"
  }' \
  --output result.png
```

**Python:**
```python
import requests

response = requests.post(
    "http://127.0.0.1:19922/api/v1/image/generate",
    json={
        "prompt": "E-sports tournament trophy with Korean text '우승'",
        "filename": "esports_trophy"
    }
)

if response.status_code == 200:
    with open("image.png", "wb") as f:
        f.write(response.content)
else:
    print(f"Error: {response.json()}")
```

**JavaScript/Node.js:**
```javascript
const prompt = "Gemini Nano Banana Pro generating a beautiful image";
const response = await fetch("http://127.0.0.1:19922/api/v1/image/generate", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ prompt, filename: "test_image" })
});

if (response.ok) {
  const buffer = await response.arrayBuffer();
  require('fs').writeFileSync('image.png', Buffer.from(buffer));
}
```

---

### `GET /health`

Check server and provider health status.

**Response (200):**
```json
{
  "status": "ok",
  "server": "browser-forge",
  "version": "1.0.0",
  "time": "2026-02-27T04:50:18.123456+09:00",
  "cdp": {
    "connected": true,
    "port": 18800,
    "host": "127.0.0.1"
  },
  "providers": {
    "gemini_nano": {
      "tab_available": true,
      "tab_url": "https://gemini.google.com/app"
    }
  }
}
```

**Example:**
```bash
curl http://127.0.0.1:19922/health | jq
```

---

## Prompt Guidelines

### For Gemini Nano Banana Pro (Current)

**Best Practices:**
- **Length:** 1-3 sentences (specific, descriptive)
- **Language:** Korean or English supported
- **Style:** vibrant, dynamic, professional
- **Resolution:** Output is always 1024x1024 square (1:1)

**Example Prompts:**

❌ **Poor:**
```
image of a person
```

✅ **Good:**
```
E-sports tournament stage with dramatic blue and purple neon lighting, 
trophy on center pedestal, crowd blur in background, professional lighting setup
```

❌ **Avoid:**
- People/faces (Gemini policy: not allowed)
- Political figures
- Violence/gore
- Copyrighted content

✅ **Focus on:**
- Esports arenas, gaming setups
- League of Legends game scenes, champion art
- Tournament stages, scoreboards
- Gaming peripherals, trophies
- Team logos, banners

**Korean Prompts:**
```
광활한 게이밍 토너먼트 아레나, 무대 중앙에 우승 트로피, 
강렬한 보라색과 파란색 네온 조명, 전자 스코어보드에 'T1' 로고
```

---

## Output Structure

Images are saved locally with this structure:

```
output/
└── YYYY-MM-DD/
    ├── 1708953618_image_browser.png
    ├── 1708953680_t1_esports_arena_browser.png
    └── ...
```

- **Folder:** Date-based organization (YYYY-MM-DD)
- **Filename:** `{unix_timestamp}_{custom_name}_browser.png`
- **Format:** PNG, 1024x1024 pixels
- **Size:** Typically 100-300 KB

---

## Architecture

### Request Flow

```
POST /api/v1/image/generate
    ↓
routes/image.py (validate request)
    ↓
core/lock.py (acquire provider lock - prevent concurrent requests)
    ↓
providers/gemini_nano.py (CDP WebSocket automation)
    │ 1. Ensure Gemini tab open
    │ 2. Click "Generate Image" button
    │ 3. Input prompt via JavaScript execution
    │ 4. Click send
    │ 5. Wait for image (up to 65 seconds)
    │ 6. Fetch image via CDP (Base64 → bytes)
    │ 7. Save to output/{date}/{timestamp}_{name}.png
    │ 8. Return PNG binary
    ↓
HTTP 200 + image/png
```

### Provider Architecture

```python
# Base provider interface
class BaseImageProvider(ABC):
    async def generate(self, prompt: str, output_path: str) -> bool:
        """Generate image and save to output_path"""
        pass
    
    @property
    def provider_name(self) -> str:
        """Return provider identifier"""
        pass

# Gemini implementation
class GeminiNanoProvider(BaseImageProvider):
    async def generate(self, prompt: str, output_path: str) -> bool:
        # CDP automation via websockets
        pass
```

**Why this design?**
- Easy to add ChatGPT (DALL-E web), Kling, Midjourney, etc.
- Swap providers without changing routes
- Each provider manages its own tab/session

---

## Configuration

Edit `config.py`:

```python
CDP_HOST = "127.0.0.1"           # Chrome DevTools Protocol host
CDP_PORT = 18800                 # Chrome DevTools Protocol port
OUTPUT_ROOT = "./output"         # Image output directory
SERVER_PORT = 19922              # API server port
```

### Running Chrome with CDP

**macOS:**
```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=18800
```

**Linux:**
```bash
google-chrome --remote-debugging-port=18800
```

**Docker (Chromium):**
```bash
docker run -d \
  -p 18800:9222 \
  ghcr.io/chromedp/headless-shell:latest \
  --remote-debugging-address=0.0.0.0 \
  --remote-debugging-port=9222
```

---

## Error Handling

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `HTTP 400: prompt cannot be empty` | Missing/empty prompt | Provide non-empty prompt string |
| `HTTP 503: Browser automation module error` | CDP not responding | Start Chrome with `--remote-debugging-port=18800` |
| `HTTP 500: Gemini탭을 찾을 수 없습니다` | Gemini tab not open | Open Chrome, go to gemini.google.com/app, log in |
| `HTTP 500: Failed to generate AI image 1 after retry` | Gemini generation failed | Retry; check prompt for blocked content (violence, people, etc.) |
| `HTTP 500: 이미지 생성 타임아웃` | Generation took >65 seconds | Retry with simpler prompt |

### Debug Mode

Add logging to server output:

```bash
LOG_LEVEL=DEBUG python server.py
```

Check `/tmp/browser-forge.log` for detailed CDP communication traces.

---

## Rate Limiting & Concurrency

- **Per-provider:** Only one request at a time (asyncio.Lock)
- **Example:** If 3 requests hit `/api/v1/image/generate` simultaneously:
  - Request A acquires lock → executes
  - Request B waits (queued)
  - Request C waits (queued)
  - Request A completes → Request B acquires lock
  - etc.

**Typical timing:**
- Fast prompt: 15-25 seconds
- Complex prompt: 30-65 seconds
- Total request time: generation time + overhead (~2-5s)

---

## Future Roadmap

### v1.1 (Next)
- [ ] Provider support: ChatGPT (DALL-E web), Kling video
- [ ] Request queue with priority levels
- [ ] Webhook callbacks for async completion notifications
- [ ] Rate limiting per IP
- [ ] API key authentication (optional)

### v2.0
- [ ] Multi-provider orchestration (parallel requests)
- [ ] Image edit mode (in-paint/out-paint)
- [ ] Batch generation with progress tracking
- [ ] S3/cloud storage integration
- [ ] Web dashboard (monitoring + manual generation)

---

## Development

### Adding a New Provider

1. Create `providers/chatgpt_dalle.py`:
   ```python
   from providers.base import BaseImageProvider
   
   class ChatGPTDALLEProvider(BaseImageProvider):
       async def generate(self, prompt: str, output_path: str) -> bool:
           # Implement DALL-E web automation
           pass
       
       @property
       def provider_name(self) -> str:
           return "chatgpt_dalle"
   ```

2. Register in `server.py`:
   ```python
   from providers.chatgpt_dalle import ChatGPTDALLEProvider
   
   app.include_router(image_router)  # Updated to support multiple providers
   ```

3. Call via API:
   ```bash
   curl -X POST http://127.0.0.1:19922/api/v1/image/generate \
     -d '{"prompt":"...", "provider":"chatgpt_dalle"}'
   ```

### Running Tests

```bash
python -m pytest tests/ -v
```

---

## Support & Contributing

- **Issues:** https://github.com/groovybottle/browser-forge/issues
- **PR:** https://github.com/groovybottle/browser-forge/pulls
- **Security:** Contact maintainer (don't public disclose)

---

## License

MIT

---

## Changelog

### v1.0.0 (2026-02-27)
- ✅ Initial release
- ✅ Gemini Nano Banana Pro image generation
- ✅ macOS + Linux support (CDP fetch method)
- ✅ Provider abstraction layer
- ✅ Health check endpoint
- ✅ Request serialization with asyncio.Lock
