"""
File and filesystem utilities for safe cross-platform file handling.
"""

import os
import re
import time
import requests


def sanitize_filename(name: str) -> str:
    """Sanitize string to be safe for Windows, Linux, and macOS file/folder names."""
    if not name:
        return "unnamed"
    # Replace illegal Windows characters: < > : " / \ | ? *
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    # Remove leading/trailing spaces and dots
    name = name.strip(' .')
    # Collapse multiple spaces or underscores
    name = re.sub(r'\s+', ' ', name)
    return name or "unnamed"


def safe_download_file(
    session: requests.Session,
    url: str,
    target_path: str,
    min_size: int = 100,
    timeout: int = 20,
    max_retries: int = 3
) -> bool:
    """
    Download a file safely with streaming, atomic write, and verification.
    Skips if destination file already exists and meets minimum size criteria.
    """
    if not url:
        return False

    if os.path.exists(target_path) and os.path.getsize(target_path) > min_size:
        return True

    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    temp_path = f"{target_path}.tmp"

    for attempt in range(max_retries):
        try:
            resp = session.get(url, stream=True, timeout=timeout)
            resp.raise_for_status()
            with open(temp_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=32768):
                    if chunk:
                        f.write(chunk)

            if os.path.exists(temp_path) and os.path.getsize(temp_path) > min_size:
                if os.path.exists(target_path):
                    os.remove(target_path)
                os.rename(temp_path, target_path)
                return True
        except Exception:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
            if attempt == max_retries - 1:
                return False
            time.sleep(1)

    return False
