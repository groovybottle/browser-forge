"""
Nano Banana Antigravity image generation provider.
Uses Gemini 3 Pro Image via existing OpenClaw Antigravity OAuth credentials.
No separate API key needed!
"""

import os
import subprocess
import sys

from providers.base import BaseImageProvider

SKILL_DIR = os.path.expanduser(
    "~/.openclaw/workspace/skills/nano-banana-antigravity"
)
GENERATE_SCRIPT = os.path.join(SKILL_DIR, "scripts", "generate_image.py")

# uv absolute path (LaunchAgent may not have /opt/homebrew/bin in PATH)
UV_BIN = "/opt/homebrew/bin/uv"
if not os.path.exists(UV_BIN):
    UV_BIN = "uv"  # fallback to PATH


class NanoBananaProvider(BaseImageProvider):
    @property
    def provider_name(self) -> str:
        return "nano_banana"

    async def generate(
        self,
        prompt: str,
        output_path: str,
        input_images: list[str] | None = None,
        aspect_ratio: str = "1:1",
        resolution: str = "2K",
    ) -> bool:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        cmd = [
            UV_BIN,
            "run",
            GENERATE_SCRIPT,
            "--prompt", prompt,
            "--filename", output_path,
            "--aspect-ratio", aspect_ratio,
            "--resolution", resolution,
        ]

        # Attach input images for editing/compositing
        if input_images:
            for img_path in input_images:
                cmd += ["--input-image", img_path]

        print(f"[nano_banana] running: {' '.join(cmd[:6])} ...", file=sys.stderr)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode != 0:
                print(f"[nano_banana] error: {result.stderr[-500:]}", file=sys.stderr)
                return False

            # Check output file
            if os.path.exists(output_path) and os.path.getsize(output_path) > 10_000:
                size = os.path.getsize(output_path)
                print(f"[nano_banana] saved: {output_path} ({size:,} bytes)", file=sys.stderr)
                return True

            print(f"[nano_banana] output file missing or too small", file=sys.stderr)
            return False

        except subprocess.TimeoutExpired:
            print("[nano_banana] timeout (120s)", file=sys.stderr)
            return False
        except Exception as e:
            print(f"[nano_banana] exception: {e}", file=sys.stderr)
            return False

    def check_tab(self) -> dict:
        """Check if nano-banana script is available."""
        available = os.path.exists(GENERATE_SCRIPT)
        return {
            "tab_available": available,
            "tab_url": GENERATE_SCRIPT if available else "",
        }
