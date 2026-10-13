"""Initialize native media tools outside the HTTP request path on Render."""
import os
from pathlib import Path
import shutil
import subprocess
import sys


def prepare_runtime():
    if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):
        import static_ffmpeg
        static_ffmpeg.add_paths()
    if os.name != 'nt' and os.getenv('VIDEO_INSTALL_BROWSER', '1') == '1':
        from playwright.sync_api import sync_playwright
        with sync_playwright() as browser:
            executable = Path(browser.chromium.executable_path)
        if not executable.is_file():
            # PIL is still available when a native host cannot run Chromium.
            subprocess.run([sys.executable, '-m', 'playwright', 'install', 'chromium'],
                           capture_output=True, timeout=240, check=False)
