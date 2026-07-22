#!/usr/bin/env python3
"""Record a browser demo of the Flowy retrieval API OpenAPI UI and flows."""

from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8000"
PDF = Path("/opt/cursor/artifacts/assets/sample-report.pdf")
OUT_DIR = Path("/tmp/demo-record")
ARTIFACT_DIR = Path("/opt/cursor/artifacts")
VIDEO_OUT = ARTIFACT_DIR / "flowy-retrieval-demo.mp4"
SCREENSHOT_DIR = ARTIFACT_DIR / "screenshots"


def pause(seconds: float = 1.2) -> None:
    time.sleep(seconds)


def open_operation(page, path_fragment: str) -> None:
    summary = page.locator(".opblock-summary").filter(has_text=path_fragment).first
    summary.scroll_into_view_if_needed()
    pause(0.3)
    summary.click()
    pause(0.8)


def execute(page) -> None:
    page.locator("button.btn.execute").last.click()
    pause(2.0)


def focus_live_response(page) -> None:
    # Swagger puts the actual HTTP response in .live-responses-table
    live = page.locator(".live-responses-table").last
    live.wait_for(state="visible", timeout=10000)
    live.scroll_into_view_if_needed()
    pause(0.8)
    # Nudge so status + body are centered
    page.evaluate(
        """() => {
          const el = document.querySelector('.live-responses-table');
          if (el) el.scrollIntoView({block: 'center', behavior: 'instant'});
        }"""
    )
    pause(1.5)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    for old in OUT_DIR.glob("*"):
        old.unlink()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            record_video_dir=str(OUT_DIR),
            record_video_size={"width": 1440, "height": 900},
        )
        page = context.new_page()

        page.goto(f"{BASE}/docs", wait_until="networkidle")
        pause(2.5)
        page.screenshot(path=str(SCREENSHOT_DIR / "01-docs.png"), full_page=False)

        # Health
        open_operation(page, "/health")
        page.locator("button", has_text="Try it out").last.click()
        pause(0.8)
        execute(page)
        focus_live_response(page)
        page.screenshot(path=str(SCREENSHOT_DIR / "02-health.png"), full_page=False)
        pause(2.0)
        open_operation(page, "/health")
        pause(0.5)

        # Upload PDF
        open_operation(page, "/api/v1/documents")
        page.locator("button", has_text="Try it out").last.click()
        pause(0.8)
        page.set_input_files('input[type="file"]', str(PDF))
        text_inputs = page.locator('.opblock.is-open input[type="text"]')
        if text_inputs.count() > 0:
            text_inputs.first.fill("demo_dataset")
        pause(1.2)
        execute(page)
        focus_live_response(page)
        page.screenshot(path=str(SCREENSHOT_DIR / "03-upload.png"), full_page=False)
        pause(2.5)
        open_operation(page, "/api/v1/documents")
        pause(0.5)

        # Query
        open_operation(page, "/api/v1/query")
        page.locator("button", has_text="Try it out").last.click()
        pause(0.8)
        body = json.dumps(
            {
                "query": "What were the key findings and risks?",
                "dataset_name": "demo_dataset",
                "search_type": "RAG_COMPLETION",
            },
            indent=2,
        )
        textarea = page.locator(".opblock.is-open textarea").first
        textarea.click()
        textarea.fill(body)
        pause(1.5)
        execute(page)
        focus_live_response(page)
        page.screenshot(path=str(SCREENSHOT_DIR / "04-query.png"), full_page=False)
        pause(3.5)

        page.close()
        context.close()
        browser.close()

    videos = list(OUT_DIR.glob("*.webm"))
    if not videos:
        raise SystemExit("No Playwright video was recorded")
    webm = max(videos, key=lambda path: path.stat().st_mtime)
    print("raw video:", webm)

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(webm),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(VIDEO_OUT),
        ],
        check=True,
    )
    print("wrote", VIDEO_OUT, "size", VIDEO_OUT.stat().st_size)


if __name__ == "__main__":
    main()
