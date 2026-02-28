"""
Gemini Nano Banana Pro image generation via CDP browser automation.
Pure CDP WebSocket - no clipboard, no peekaboo, no OS-specific dependencies.
"""

import asyncio
import base64
import json
import os
import sys
import time
import urllib.request

import websockets

from config import CDP_HOST, CDP_PORT
from providers.base import BaseImageProvider

CDP_HTTP = f"http://{CDP_HOST}:{CDP_PORT}"


def get_tabs() -> list:
    try:
        with urllib.request.urlopen(f"{CDP_HTTP}/json", timeout=5) as resp:
            return json.loads(resp.read())
    except Exception as e:
        print(f"[gemini_nano] tab list failed: {e}", file=sys.stderr)
        return []


def find_gemini_tab() -> dict | None:
    for tab in get_tabs():
        if "gemini.google.com" in tab.get("url", "") and tab.get("type") == "page":
            return tab
    return None


def ensure_gemini_tab(wait_sec: float = 10.0) -> dict | None:
    """Find existing Gemini tab or open a new one via CDP."""
    tab = find_gemini_tab()
    if tab:
        print(f"[gemini_nano] reusing tab: {tab['url'][:60]}", file=sys.stderr)
        return tab

    print("[gemini_nano] no Gemini tab, opening new one...", file=sys.stderr)
    try:
        req = urllib.request.Request(
            f"{CDP_HTTP}/json/new?https://gemini.google.com/app",
            method="PUT",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            new_tab = json.loads(resp.read())
            print(f"[gemini_nano] new tab: {new_tab.get('id', '?')}", file=sys.stderr)
    except Exception as e:
        print(f"[gemini_nano] tab creation failed: {e}", file=sys.stderr)
        return None

    for i in range(int(wait_sec)):
        time.sleep(1)
        tab = find_gemini_tab()
        if tab and "gemini.google.com/app" in tab.get("url", ""):
            print(f"[gemini_nano] tab ready after {i + 1}s", file=sys.stderr)
            time.sleep(2)
            return tab

    tab = find_gemini_tab()
    if tab:
        return tab

    print("[gemini_nano] tab load timeout", file=sys.stderr)
    return None


async def cdp(ws, method: str, params: dict = None, timeout: float = 30) -> dict:
    """Send a CDP command and wait for the matching response."""
    cmd_id = int(time.time() * 1000) % 999999 + 1
    msg = {"id": cmd_id, "method": method}
    if params:
        msg["params"] = params
    await ws.send(json.dumps(msg))

    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            raw = await asyncio.wait_for(ws.recv(), timeout=1.0)
            data = json.loads(raw)
            if data.get("id") == cmd_id:
                return data
        except asyncio.TimeoutError:
            continue
    raise TimeoutError(f"CDP timeout: {method}")


async def wait_for_new_image(ws, prev_img_src: str | None, timeout: float = 65) -> str | None:
    """Poll DOM until a new AI-generated image appears."""
    js = """
    (function() {
        const selectors = [
            'img[alt*="AI generated"]',
            'img[alt*="ai generated"]',
            '.response-container img',
            'model-response img[src*="googleusercontent"]',
        ];
        for (const sel of selectors) {
            const imgs = document.querySelectorAll(sel);
            for (const img of imgs) {
                if (img.naturalWidth > 100 && img.src && img.src.includes('googleusercontent')) {
                    return img.src;
                }
            }
        }
        const allImgs = document.querySelectorAll('img[src*="gg-dl"]');
        for (const img of allImgs) {
            if (img.naturalWidth > 100) return img.src;
        }
        return null;
    })()
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        result = await cdp(ws, "Runtime.evaluate", {"expression": js}, timeout=5)
        src = result.get("result", {}).get("result", {}).get("value")
        if src and src != prev_img_src:
            return src
        await asyncio.sleep(1.5)
    return None


async def fetch_image_via_cdp(ws, img_url: str) -> bytes | None:
    """Fetch image bytes: try direct download first, then CDP cookie extraction."""
    # 1) Direct download (no cookies) — signed URLs work without auth
    try:
        req = urllib.request.Request(img_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read()
            if len(data) > 10_000:
                print(f"[gemini_nano] direct download ok ({len(data):,} bytes)", file=sys.stderr)
                return data
    except Exception as e:
        print(f"[gemini_nano] direct download failed: {e}", file=sys.stderr)

    # 2) Extract cookies from CDP and download with them
    try:
        from urllib.parse import urlparse
        parsed = urlparse(img_url)
        cookie_domain = f"https://{parsed.netloc}"
        res = await cdp(ws, "Network.getCookies", {"urls": [cookie_domain, "https://gemini.google.com"]}, timeout=5)
        cookies = res.get("result", {}).get("cookies", [])
        cookie_str = "; ".join(f"{c['name']}={c['value']}" for c in cookies)
        print(f"[gemini_nano] got {len(cookies)} cookies, downloading...", file=sys.stderr)
        req = urllib.request.Request(img_url, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Referer": "https://gemini.google.com/",
            "Cookie": cookie_str,
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read()
            if len(data) > 10_000:
                print(f"[gemini_nano] cookie download ok ({len(data):,} bytes)", file=sys.stderr)
                return data
    except Exception as e:
        print(f"[gemini_nano] cookie download failed: {e}", file=sys.stderr)

    # 3) Canvas toDataURL fallback (may fail on CORS-tainted images)
    js = f"""
    (async function() {{
        try {{
            const img = new Image();
            img.crossOrigin = 'anonymous';
            await new Promise((resolve, reject) => {{
                img.onload = resolve; img.onerror = reject;
                img.src = "{img_url}";
            }});
            const canvas = document.createElement('canvas');
            canvas.width = img.naturalWidth || 1024;
            canvas.height = img.naturalHeight || 1024;
            canvas.getContext('2d').drawImage(img, 0, 0);
            const dataUrl = canvas.toDataURL('image/png');
            return dataUrl.includes(',') ? dataUrl.split(',')[1] : 'CANVAS_ERROR:empty';
        }} catch(e) {{
            return 'CANVAS_ERROR:' + e.message;
        }}
    }})()
    """
    result = await cdp(
        ws,
        "Runtime.evaluate",
        {"expression": js, "awaitPromise": True, "timeout": 20000},
        timeout=30,
    )
    val = result.get("result", {}).get("result", {}).get("value")
    if val and not val.startswith("CANVAS_ERROR"):
        print(f"[gemini_nano] canvas fallback ok", file=sys.stderr)
        return base64.b64decode(val)
    print(f"[gemini_nano] all fetch methods failed: {val}", file=sys.stderr)
    return None


class GeminiNanoProvider(BaseImageProvider):
    @property
    def provider_name(self) -> str:
        return "gemini_nano"

    async def generate(self, prompt: str, output_path: str, input_images: list[str] | None = None) -> bool:
        tab = ensure_gemini_tab(wait_sec=15.0)
        if not tab:
            print("[gemini_nano] cannot open Gemini tab", file=sys.stderr)
            return False

        ws_url = tab["webSocketDebuggerUrl"]
        print(f"[gemini_nano] tab: {tab['url'][:60]}", file=sys.stderr)

        async with websockets.connect(ws_url, max_size=50 * 1024 * 1024) as ws:
            # Remember current image src to detect new one
            current_js = """
            (function() {
                const img = document.querySelector('img[src*="gg-dl"]');
                return img ? img.src : null;
            })()
            """
            prev = (
                (await cdp(ws, "Runtime.evaluate", {"expression": current_js}))
                .get("result", {})
                .get("result", {})
                .get("value")
            )

            # Click "New chat" and wait for UI to load
            new_chat_js = """
            (function() {
                const links = document.querySelectorAll('a[href="/app"]');
                for (const link of links) {
                    if (link.textContent.includes('새 채팅') || link.textContent.includes('New chat')) {
                        link.click();
                        return 'new_chat_clicked';
                    }
                }
                if (links.length > 0) {
                    links[links.length - 1].click();
                    return 'new_chat_fallback_clicked';
                }
                return 'new_chat_not_found';
            })()
            """
            await cdp(ws, "Runtime.evaluate", {"expression": new_chat_js})
            await asyncio.sleep(3)  # 새 채팅 화면 완전 로드 대기

            # Click "이미지 만들기" button (activate image generation mode)
            # aria-label: '🍌 이미지 만들기, 버튼, 탭하여 도구 사용'
            # If already active, aria-label contains '선택 해제' — skip click in that case
            img_gen_btn_js = """
            (function() {
                const btns = document.querySelectorAll('button, [role="button"]');
                for (const btn of btns) {
                    const aria = btn.getAttribute('aria-label') || '';
                    const text = btn.textContent.trim();
                    const hasImageCreate = aria.includes('이미지 만들기') || text.includes('이미지 만들기') ||
                                          aria.includes('Create image') || aria.includes('Generate image');
                    if (!hasImageCreate) continue;
                    // If '선택 해제' in aria → already active, skip click
                    if (aria.includes('선택 해제') || aria.includes('deselect') || aria.includes('Deselect')) {
                        return 'image_btn_already_active:' + aria.substring(0, 60);
                    }
                    btn.click();
                    return 'image_btn_clicked:' + aria.substring(0, 60);
                }
                return 'image_gen_btn_not_found';
            })()
            """
            result = await cdp(ws, "Runtime.evaluate", {"expression": img_gen_btn_js})
            img_btn_val = result.get("result", {}).get("result", {}).get("value", "")
            print(f"[gemini_nano] image btn: {img_btn_val}", file=sys.stderr)
            if "not_found" in img_btn_val:
                print("[gemini_nano] WARNING: '이미지 만들기' button not found!", file=sys.stderr)
            await asyncio.sleep(2.5)  # Wait for image mode UI (mode selector) to appear

            # Open "모드 선택" dropdown first (shows "빠른 모드" by default)
            mode_dropdown_js = """
            (function() {
                const btns = document.querySelectorAll('button');
                for (const btn of btns) {
                    const aria = btn.getAttribute('aria-label') || '';
                    const text = btn.textContent.trim();
                    if (aria === '모드 선택 도구 열기' || aria.includes('모드 선택') || text === '빠른 모드' || text === 'Fast mode') {
                        btn.click();
                        return 'mode_dropdown_clicked:' + aria + ' | ' + text.substring(0, 30);
                    }
                }
                return 'mode_dropdown_not_found';
            })()
            """
            result = await cdp(ws, "Runtime.evaluate", {"expression": mode_dropdown_js})
            mode_val = result.get("result", {}).get("result", {}).get("value", "")
            print(f"[gemini_nano] mode dropdown: {mode_val}", file=sys.stderr)
            await asyncio.sleep(1.2)  # Wait for dropdown to open

            # Click "Pro" option inside the dropdown (mat-mdc-menu-item with 'Pro' text)
            pro_option_js = """
            (function() {
                // Look in menuitemradio buttons (mat-menu items)
                const menuItems = document.querySelectorAll('button[role="menuitemradio"], .mat-mdc-menu-item, [role="menuitem"]');
                for (const btn of menuItems) {
                    const text = btn.textContent.trim();
                    // Match 'Pro' but NOT '빠른 모드' or 'Fast'
                    if (text.toLowerCase().includes('pro') && !text.includes('빠른') && !text.toLowerCase().includes('fast')) {
                        // Check if already selected
                        const checked = btn.getAttribute('aria-checked') || btn.getAttribute('aria-selected') || '';
                        if (checked === 'true') return 'pro_already_selected';
                        btn.click();
                        return 'pro_option_clicked:' + text.substring(0, 40);
                    }
                }
                // Fallback: find any visible element with text 'Pro' or 'PRO' and click its clickable parent
                const spans = document.querySelectorAll('span.mode-title');
                for (const span of spans) {
                    const text = span.textContent.trim();
                    if (text === 'Pro' || text === 'PRO') {
                        let el = span;
                        for (let i = 0; i < 6; i++) {
                            el = el.parentElement;
                            if (!el) break;
                            if (el.tagName === 'BUTTON' || el.getAttribute('role') === 'menuitemradio') {
                                el.click();
                                return 'pro_parent_clicked:' + text;
                            }
                        }
                    }
                }
                return 'pro_option_not_found';
            })()
            """
            result = await cdp(ws, "Runtime.evaluate", {"expression": pro_option_js})
            pro_val = result.get("result", {}).get("result", {}).get("value", "")
            print(f"[gemini_nano] pro option: {pro_val}", file=sys.stderr)
            if "clicked" in pro_val or "selected" in pro_val:
                await asyncio.sleep(0.8)

            # Attach reference images via ClipboardEvent paste injection
            if input_images:
                print(f"[gemini_nano] attaching {len(input_images)} reference image(s)...", file=sys.stderr)
                for img_path in input_images:
                    abs_path = os.path.abspath(img_path)
                    if not os.path.exists(abs_path):
                        print(f"[gemini_nano] WARNING: image not found: {abs_path}", file=sys.stderr)
                        continue

                    # Read image and encode as base64
                    with open(abs_path, "rb") as f:
                        img_b64 = base64.b64encode(f.read()).decode()

                    ext = os.path.splitext(abs_path)[1].lower()
                    mime = {"jpg": "image/jpeg", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                            ".png": "image/png", ".webp": "image/webp", ".gif": "image/gif"}.get(ext, "image/png")
                    fname = os.path.basename(abs_path)

                    paste_js = f"""
                    (async function() {{
                        try {{
                            const b64 = "{img_b64}";
                            const bytes = atob(b64);
                            const arr = new Uint8Array(bytes.length);
                            for (let i = 0; i < bytes.length; i++) arr[i] = bytes.charCodeAt(i);
                            const blob = new Blob([arr], {{type: '{mime}'}});
                            const file = new File([blob], '{fname}', {{type: '{mime}'}});

                            const dt = new DataTransfer();
                            dt.items.add(file);

                            const editor = document.querySelector('rich-textarea') ||
                                           document.querySelector('[contenteditable="true"]');
                            if (!editor) return 'editor_not_found';

                            const pasteEvent = new ClipboardEvent('paste', {{
                                clipboardData: dt,
                                bubbles: true,
                                cancelable: true
                            }});
                            editor.dispatchEvent(pasteEvent);
                            return 'paste_ok:{fname}';
                        }} catch(e) {{
                            return 'paste_error:' + e.message;
                        }}
                    }})()
                    """
                    result = await cdp(ws, "Runtime.evaluate", {"expression": paste_js, "awaitPromise": True}, timeout=15)
                    paste_val = result.get("result", {}).get("result", {}).get("value", "")
                    print(f"[gemini_nano] image paste: {paste_val}", file=sys.stderr)
                    await asyncio.sleep(1.5)  # Wait for thumbnail to render

            # Type prompt
            escaped = prompt.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")
            input_js = f"""
            (function() {{
                const editors = [
                    document.querySelector('rich-textarea [contenteditable]'),
                    document.querySelector('[contenteditable="true"]'),
                    document.querySelector('textarea'),
                ];
                for (const el of editors) {{
                    if (!el) continue;
                    el.focus();
                    if (el.tagName === 'TEXTAREA') {{
                        const setter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set;
                        setter.call(el, "{escaped}");
                        el.dispatchEvent(new Event('input', {{bubbles: true}}));
                    }} else {{
                        document.execCommand('selectAll', false, null);
                        document.execCommand('delete', false, null);
                        document.execCommand('insertText', false, "{escaped}");
                        el.dispatchEvent(new InputEvent('input', {{bubbles: true}}));
                    }}
                    return 'input_ok:' + el.tagName;
                }}
                return 'input_not_found';
            }})()
            """
            result = await cdp(ws, "Runtime.evaluate", {"expression": input_js})
            inp_val = result.get("result", {}).get("result", {}).get("value", "")
            if "not_found" in inp_val:
                print("[gemini_nano] input field not found", file=sys.stderr)
                return False

            await asyncio.sleep(0.5)

            # Click send
            send_js = """
            (function() {
                const btns = document.querySelectorAll('button');
                for (const btn of btns) {
                    const aria = (btn.getAttribute('aria-label') || '').toLowerCase();
                    if (aria.includes('send') || aria.includes('메시지 보내기') || aria.includes('보내기')) {
                        btn.click();
                        return 'send_clicked:' + aria;
                    }
                }
                return 'send_not_found';
            })()
            """
            await cdp(ws, "Runtime.evaluate", {"expression": send_js})
            await asyncio.sleep(0.5)

            # Wait for new image
            print("[gemini_nano] waiting for image (up to 65s)...", file=sys.stderr)
            img_url = await wait_for_new_image(ws, prev_img_src=prev, timeout=65)
            if not img_url:
                print("[gemini_nano] image generation timeout", file=sys.stderr)
                return False

            print(f"[gemini_nano] image URL: {img_url[:70]}...", file=sys.stderr)

            # Fetch image via CDP and save to file
            img_bytes = await fetch_image_via_cdp(ws, img_url)
            if not img_bytes:
                return False

            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(img_bytes)

            size = len(img_bytes)
            print(f"[gemini_nano] saved: {output_path} ({size:,} bytes)", file=sys.stderr)
            return size > 10_000

    def check_tab(self) -> dict:
        """Check if a Gemini tab is available (for health endpoint)."""
        tab = find_gemini_tab()
        if tab:
            return {"tab_available": True, "tab_url": tab.get("url", "")}
        return {"tab_available": False, "tab_url": ""}
