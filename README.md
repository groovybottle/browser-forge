# browser-forge

> 🔮 CDP(Chrome DevTools Protocol) 기반 AI 서비스 자동화 서버
> 
> API 키 없이 브라우저로 Gemini, ChatGPT, DALL-E, Kling 등을 개인 서버처럼 운영하세요.

[![GitHub](https://img.shields.io/badge/GitHub-groovybottle/browser--forge-blue)](https://github.com/groovybottle/browser-forge)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)

---

## 🎯 개요

browser-forge는 **로그인된 브라우저를 CDP(Chrome DevTools Protocol)로 제어**해서 AI 서비스(Gemini, ChatGPT 등)에 접근하는 개인 자동화 서버입니다.

### 핵심 특징

- 🪄 **API 키 불필요** — 브라우저 세션으로 AI 기능 사용
- 🔒 **개인 운영** — 로컬/VPS에서 안전하게 실행
- 🌐 **크로스플랫폼** — macOS + Linux 지원 (Windows 예정)
- 🔌 **확장성** — Provider 추상화로 쉬운 AI 서비스 통합
- ⚡ **비동기 처리** — asyncio 기반 고성능 요청 처리
- 📦 **모듈식 구조** — 기능별 분리된 코드

### 현재 지원

| 서비스 | 기능 | 상태 |
|------|------|------|
| **Gemini** | Image Generation (Nano Banana Pro) | ✅ v1.0 |
| **ChatGPT (DALL-E)** | Image Generation via Web | 🚧 v1.1 |
| **Kling** | Video Generation via Web | 🚧 v1.1 |
| **Claude (Web)** | Text/Code Generation | 🚧 Future |
| **Midjourney** | Premium Image Generation | 🚧 Future |

---

## 🚀 빠른 시작

### 필수 요구사항

- **OS:** macOS 또는 Linux
- **Python:** 3.10 이상
- **Chrome:** 최신 버전 (--remote-debugging-port 지원)
- **브라우저 로그인:** Gemini(gemini.google.com/app)에 로그인된 상태

### 설치

```bash
# 1. 클론
git clone https://github.com/groovybottle/browser-forge.git
cd browser-forge

# 2. 의존성 설치
pip install -r requirements.txt
# 또는 venv 사용
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
pip install -r requirements.txt

# 3. 서버 시작
chmod +x start.sh
./start.sh
```

### Chrome 실행 (별도 터미널)

**macOS:**
```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=18800
```

**Linux:**
```bash
google-chrome --remote-debugging-port=18800
```

그 후 브라우저에서 `gemini.google.com/app` 방문 후 로그인하세요.

### 테스트

```bash
# 1. 서버 헬스체크
curl http://127.0.0.1:19922/health | jq

# 2. 이미지 생성
curl -X POST http://127.0.0.1:19922/api/v1/image/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt":"A vibrant esports arena with neon lights"}' \
  --output image.png

# 3. 생성된 이미지 확인
open image.png  # macOS
```

---

## 📖 API 문서

전체 API 명세는 **[API.md](API.md)** 참고.

### 주요 엔드포인트

#### `POST /api/v1/image/generate`

Gemini Nano Banana Pro로 이미지 생성

```bash
curl -X POST http://127.0.0.1:19922/api/v1/image/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "League of Legends 토너먼트 무대, 우승 트로피, 네온 조명",
    "filename": "lol_trophy_2026"
  }' \
  --output result.png
```

**Request:**
```json
{
  "prompt": "string (필수)",
  "filename": "string (선택, 기본: image)",
  "provider": "string (선택, 기본: gemini_nano)"
}
```

**Response:** PNG 이미지 (1024x1024)

#### `GET /health`

서버 상태 및 provider 헬스체크

```bash
curl http://127.0.0.1:19922/health
```

**Response:**
```json
{
  "status": "ok",
  "server": "browser-forge",
  "version": "1.0.0",
  "cdp": {
    "connected": true,
    "port": 18800
  },
  "providers": {
    "gemini_nano": {
      "tab_available": true,
      "tab_url": "https://gemini.google.com/app"
    }
  }
}
```

---

## 📐 아키텍처

### 디렉토리 구조

```
browser-forge/
├── server.py                 # FastAPI 메인 진입점
├── config.py                 # 설정 (CDP 포트, 경로 등)
├── requirements.txt          # Python 의존성
├── start.sh                  # 서버 시작 스크립트
├── core/
│   └── lock.py              # Provider별 asyncio.Lock 관리
├── providers/
│   ├── base.py              # BaseImageProvider 추상 클래스
│   └── gemini_nano.py       # Gemini CDP 자동화 구현
├── routes/
│   ├── image.py             # POST /api/v1/image/generate
│   └── health.py            # GET /health
├── output/                  # 생성된 이미지 저장 (날짜별)
├── API.md                   # 상세 API 문서
└── README.md               # 이 파일
```

### 요청 흐름

```
클라이언트 요청
    ↓
[routes/image.py] 검증 & 요청 파싱
    ↓
[core/lock.py] Provider 락 획득 (동시 요청 방지)
    ↓
[providers/gemini_nano.py] CDP 자동화
    ├─ 1. Gemini 탭 확인 (없으면 자동 열기)
    ├─ 2. "이미지 생성" 버튼 클릭
    ├─ 3. 프롬프트 입력 (JavaScript 실행)
    ├─ 4. 전송 버튼 클릭
    ├─ 5. 이미지 생성 대기 (최대 65초)
    ├─ 6. 이미지 URL 추출
    ├─ 7. CDP fetch로 바이너리 다운로드 (Base64 디코딩)
    ├─ 8. output/{YYYY-MM-DD}/{timestamp}_{name}.png 저장
    └─ 9. 응답
    ↓
HTTP 200 + image/png 바이너리 반환
```

### Provider 추상화

```python
# 모든 provider가 구현해야 하는 인터페이스
class BaseImageProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str, output_path: str) -> bool:
        """이미지 생성 및 저장"""
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Provider 이름 (API에서 참조)"""
        pass
```

**이점:**
- 새로운 AI 서비스 추가 시 `BaseImageProvider` 상속만 하면 됨
- 라우트 코드 변경 불필요
- 각 provider가 자신의 탭/세션 관리

---

## 🔧 설정

`config.py`에서 수정:

```python
# CDP (Chrome DevTools Protocol)
CDP_HOST = "127.0.0.1"           # CDP 호스트
CDP_PORT = 18800                 # CDP 포트
TIMEOUT_SECONDS = 65             # 이미지 생성 최대 대기 시간

# 서버
SERVER_HOST = "127.0.0.1"        # API 서버 바인드 주소
SERVER_PORT = 19922              # API 서버 포트

# 저장
OUTPUT_ROOT = "./output"         # 이미지 저장 디렉토리
MAX_IMAGE_SIZE_MB = 50           # 최대 이미지 크기
```

---

## 💡 프롬프트 팁

### Gemini Nano Banana Pro 최적화

**좋은 프롬프트:**
```
E-sports 토너먼트 무대, 중앙에 우승 트로피, 
강렬한 보라색 & 파란색 네온 조명, 전자 스코어보드에 'T1' 로고
```

**피해야 할 것:**
- ❌ 사람/얼굴 (Gemini 정책)
- ❌ 폭력/총기/흉기
- ❌ 정치인 이름/정치 내용
- ❌ 저작권 콘텐츠 (유명인 등)

**추천 주제:**
- 이스포츠 아레나, 게이밍 환경
- 리그 오브 레전드 게임 장면, 챔피언 아트
- 토너먼트 무대, 스코어보드
- 게이밍 주변기기, 트로피
- 팀 로고, 배너, 기치

### 한국어 프롬프트 예제

```
광활한 게임 토너먼트 무대, 무대 중앙 우승 트로피, 
강렬한 보라색과 파란색 네온 조명, 전자 스코어보드에 한국어 '우승' 문구
```

---

## 📊 모니터링

### 로그 확인

```bash
# 기본 (INFO 레벨)
./start.sh

# 디버그 모드 (DEBUG 레벨)
DEBUG=true python server.py

# 특정 로그 필터링
./start.sh 2>&1 | grep "gemini"
```

### 생성된 이미지

```
output/
├── 2026-02-27/
│   ├── 1708953618_image_browser.png
│   ├── 1708953680_t1_esports_arena_browser.png
│   └── ...
├── 2026-02-28/
│   ├── 1708954000_lol_battle_browser.png
│   └── ...
```

**명명 규칙:** `{타임스탐프}_{파일명}_{방식}.png`

---

## 🛠️ 개발

### 새로운 Provider 추가

**1. Provider 클래스 작성**

`providers/chatgpt_dalle.py`:
```python
from providers.base import BaseImageProvider
import asyncio

class ChatGPTDALLEProvider(BaseImageProvider):
    async def generate(self, prompt: str, output_path: str) -> bool:
        # DALL-E 웹 자동화 로직
        pass
    
    @property
    def provider_name(self) -> str:
        return "chatgpt_dalle"
```

**2. 라우트에 등록**

`routes/image.py`:
```python
from providers.chatgpt_dalle import ChatGPTDALLEProvider

PROVIDERS = {
    "gemini_nano": GeminiNanoProvider(),
    "chatgpt_dalle": ChatGPTDALLEProvider(),
}
```

**3. API로 호출**

```bash
curl -X POST http://127.0.0.1:19922/api/v1/image/generate \
  -d '{"prompt":"...","provider":"chatgpt_dalle"}'
```

### 테스트

```bash
pytest tests/ -v
pytest tests/test_providers.py::test_gemini -v
```

---

## 🐛 트러블슈팅

| 문제 | 원인 | 해결 |
|------|------|------|
| `HTTP 503: CDP 포트 연결 실패` | Chrome 미실행 | `--remote-debugging-port=18800`으로 Chrome 시작 |
| `Gemini 탭을 찾을 수 없음` | 탭이 닫혀있음 | Chrome에서 gemini.google.com/app 방문 + 로그인 |
| `생성 타임아웃 (65초 초과)` | 프롬프트 너무 복잡 | 더 간단한 프롬프트 사용 |
| `폭력성 단어 에러` | 블록된 콘텐츠 | "폭력", "총", "칼" 등 제거 |

---

## 📅 로드맵

### v1.1 (예정)
- [ ] ChatGPT (DALL-E web) 지원
- [ ] Kling (비디오 생성) 지원
- [ ] 웹훅 콜백 (비동기 완료 알림)
- [ ] 배치 이미지 생성 (다중 프롬프트)

### v2.0 (장기)
- [ ] 웹 대시보드 (모니터링 + 수동 생성)
- [ ] S3/클라우드 스토리지 통합
- [ ] API 인증 (API 키)
- [ ] 이미지 편집 (in-paint, out-paint)
- [ ] 속도 제한 (Rate Limiting)

---

## 🤝 기여

버그 신고 및 기능 제안:
- **Issues:** https://github.com/groovybottle/browser-forge/issues
- **Pull Requests:** https://github.com/groovybottle/browser-forge/pulls

---

## 📜 라이선스

MIT License - 자유롭게 사용, 수정, 배포 가능.

---

## 🙏 감사의 말

- **Gemini Nano Banana Pro** — Google의 강력한 이미지 생성 AI
- **CDP (Chrome DevTools Protocol)** — 브라우저 자동화의 근간
- **FastAPI** — 고성능 API 프레임워크
- **groovybottle team** — 함께 만드는 자동화 서버

---

## 📞 문의

- **Discord:** [groovybottle community]
- **Email:** Contact maintainer
- **GitHub Issues:** https://github.com/groovybottle/browser-forge/issues

---

**Made with 🔮 by [groovybottle](https://github.com/groovybottle)**
