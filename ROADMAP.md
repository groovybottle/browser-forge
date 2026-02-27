# browser-forge 로드맵 & 확장 서비스

## 🎯 핵심 목표
API 키 없이 브라우저 자동화로 무료 AI/미디어 서비스 통합

---

## 📦 v1.0 (현재)
- ✅ Gemini Nano Banana Pro (이미지 생성)
- ✅ FastAPI 기본 구조
- ✅ Health check + 에러 처리

---

## 🚀 v1.1 (우선순위)

### 1️⃣ **TTS (Text-to-Speech)** - 가장 시급
**필요성**: t1-news에서 현재 Typecast TTS 사용 → 웹 기반으로 대체 가능
**방법**: 
- Google Translate 웹 TTS (무료)
- Microsoft Edge TTS (Windows)
- Natural Reader 웹 (무료 제한)

**엔드포인트**:
```
POST /api/v1/tts/generate
{
  "text": "한국어 또는 English",
  "lang": "ko-KR",
  "speed": 1.0,
  "voice": "female|male"
}
Response: audio/mp3
```

**구현 난이도**: ⭐⭐ (쉬움)
**예상 개발 시간**: 2-3시간

---

### 2️⃣ **이미지 스크린샷 & PDF 변환**
**필요성**: 웹페이지를 이미지/PDF로 변환 (나중에 영상 커버 생성 등)
**방법**: Chrome CDP + Puppeteer 방식

**엔드포인트**:
```
POST /api/v1/screenshot/capture
{
  "url": "https://example.com",
  "format": "png|pdf",
  "width": 1920,
  "height": 1080
}
```

**구현 난이도**: ⭐⭐ (쉬움)
**예상 개발 시간**: 3-4시간

---

### 3️⃣ **번역 (Translation)**
**필요성**: 다국어 자동 번역 (한영, 영한 등)
**방법**: 
- Google Translate 웹 (무료)
- Microsoft Translator (무료)
- DeepL (무료 제한)

**엔드포인트**:
```
POST /api/v1/translate/text
{
  "text": "번역할 텍스트",
  "from": "ko",
  "to": "en"
}
Response: { "translated": "Translated text" }
```

**구현 난이도**: ⭐ (매우 쉬움)
**예상 개발 시간**: 2시간

---

## 🎬 v2.0 (확장)

### 4️⃣ **이미지 편집**
**필요성**: 이미지 자르기, 크기 조정, 필터 등
**방법**: 
- Photopea (Photoshop 호환 웹앱)
- Pixlr Editor (무료 온라인 에디터)
- Canvas.js 기반 custom

**엔드포인트**:
```
POST /api/v1/image/edit
{
  "input_url": "image URL",
  "operations": [
    {"type": "resize", "width": 1024, "height": 1024},
    {"type": "crop", "x": 0, "y": 0, "w": 512, "h": 512},
    {"type": "filter", "name": "grayscale"}
  ]
}
Response: image/png
```

**구현 난이도**: ⭐⭐⭐ (중간)
**예상 개발 시간**: 6-8시간

---

### 5️⃣ **음성 생성 (Speech Synthesis)**
**필요성**: 더 나은 품질의 TTS (자연스러운 목소리)
**방법**:
- Microsoft Edge TTS (한국어 지원 좋음)
- AWS Polly (프리 티어)
- Google Cloud TTS (300만자 무료)

**엔드포인트**:
```
POST /api/v1/speech/synthesize
{
  "text": "합성할 텍스트",
  "lang": "ko-KR",
  "voice": "google-neural|edge-tts",
  "speed": 1.0,
  "pitch": 1.0
}
Response: audio/wav or audio/mp3
```

**구현 난이도**: ⭐⭐ (쉬움)
**예상 개발 시간**: 4-5시간

---

### 6️⃣ **비디오 정보 추출**
**필요성**: YouTube 영상 메타데이터, 자막 추출
**방법**:
- youtube-dl + 브라우저 자동화
- 영상 제목, 설명, 자막 추출

**엔드포인트**:
```
POST /api/v1/video/metadata
{
  "url": "https://youtube.com/watch?v=...",
  "include": ["title", "description", "subtitles", "duration"]
}
Response: JSON metadata
```

**구현 난이도**: ⭐⭐⭐ (중간)
**예상 개발 시간**: 5-6시간

---

## 🎨 v3.0 (미래)

### 7️⃣ **웹 기반 비디오 편집**
**필요성**: 영상 자르기, 효과 추가, 자막 삽입
**방법**:
- FFmpeg CLI (로컬 처리)
- Shotcut / OpenShot 자동화
- Custom WebCodecs

**복잡도**: ⭐⭐⭐⭐⭐ (매우 복잡)

---

### 8️⃣ **다국어 음성 인식 (STT)**
**필요성**: 영상 자막 자동 생성
**방법**:
- Google Cloud Speech-to-Text (프리 티어)
- Whisper API (OpenAI, 유료)
- Azure Speech Services (프리 티어)

---

### 9️⃣ **고급 이미지 생성**
**필요성**: Gemini 외 다른 모델 지원
**방법**:
- DALL-E 웹 자동화
- Kling 동영상 생성
- Midjourney Discord 자동화 (불안정)

---

## 📊 t1-news 통합 시나리오

### 현재 파이프라인
```
Google News
  ↓ (GPT 필터링)
스크립트 생성 (GPT)
  ↓ (GPT)
이미지 프롬프트 생성
  ↓ (Gemini web)
이미지 생성 [← browser-forge v1.0]
  ↓ (Typecast)
TTS 생성 [← 현재: Typecast]
  ↓ (FFmpeg)
영상 합성
  ↓
YouTube 업로드
```

### 개선된 파이프라인 (v1.1+)
```
Google News
  ↓ (GPT)
스크립트 생성 + 번역 [← browser-forge v1.1]
  ↓ (GPT)
이미지 프롬프트 생성 + 번역
  ↓ (Gemini web)
이미지 생성 [← v1.0]
  ↓ (Google Translate TTS)
TTS 생성 (한국어 + 영어) [← v1.1 대체]
  ↓ (FFmpeg)
영상 합성 + 로고 오버레이 [← v2.0 이미지 편집]
  ↓
YouTube 업로드 + 자동 자막 [← v2.0]
```

---

## 💡 우선순위 분석

### 즉시 필요 (v1.1 - 이번주)
1. **TTS** ⭐⭐⭐ - Typecast 대체, 비용 절감
2. **번역** ⭐⭐ - 다국어 지원 필요

### 중기 필요 (v1.2 - 다음주)
3. **스크린샷** ⭐⭐ - 커버 이미지 생성
4. **이미지 편집** ⭐⭐⭐ - 영상 인트로/아웃트로

### 장기 계획 (v2.0+)
5. **음성 생성** ⭐⭐
6. **비디오 정보** ⭐⭐
7. **고급 기능들**

---

## 🛠️ 기술 스택

### TTS 구현 (v1.1 우선)
**Google Translate TTS**:
```python
# 무료 (속도 제한 있음)
# 단순 HTTP 요청으로 음성 파일 획득
# 다국어 지원
# 1MB 미만 음성 생성 권장
```

**Edge TTS**:
```python
# Microsoft 제공 (무료)
# 한국어 음성 품질 우수
# 장문 지원 (2만자 이상)
```

---

## 📝 예상 개발 시간

| 버전 | 기능 | 소요 시간 | 난이도 |
|------|------|---------|--------|
| v1.1 | TTS | 2-3h | ⭐⭐ |
| v1.1 | 번역 | 2h | ⭐ |
| v1.2 | 스크린샷 | 3-4h | ⭐⭐ |
| v1.2 | 이미지 편집 | 6-8h | ⭐⭐⭐ |
| v2.0 | 음성 생성 | 4-5h | ⭐⭐ |
| v2.0 | 비디오 정보 | 5-6h | ⭐⭐⭐ |

**총 예상**: 약 22-31시간 (모든 v1.x + v2.0)

---

## 🎯 다음 단계

**즉시 (오늘)**:
1. Gemini 이미지 생성 로그인 해결
2. v1.0 테스트 완료

**이번주 (v1.1)**:
1. TTS provider 구현 (Google Translate 또는 Edge)
2. 번역 provider 구현 (Google Translate)
3. API 테스트

**다음주 (v1.2)**:
1. 스크린샷 기능
2. 이미지 편집

---

## ❓ 두목님의 우선순위는?

어느 서비스부터 추가하고 싶으신가요?

1. **TTS** - Typecast 대체 (비용 절감)
2. **번역** - 다국어 지원
3. **스크린샷** - 커버 이미지
4. **이미지 편집** - 고급 기능
5. **음성 생성** - 품질 개선
6. **기타**

선택해주세요! 🚀
