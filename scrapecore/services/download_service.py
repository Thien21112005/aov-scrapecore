"""
Download Service: Manages concurrent asset downloading and local caching.
"""

import os
import json
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

from ..core.models import DownloadResult
from ..utils.file_utils import sanitize_filename, safe_download_file


def _safe_callback(callback, hero_name, item_name, ok, is_hero_finished=False):
    """Safely invoke callback with varying signatures."""
    if not callback:
        return
    try:
        callback(hero_name, item_name, ok, is_hero_finished)
    except TypeError:
        try:
            callback(hero_name, item_name, ok)
        except TypeError:
            try:
                callback(item_name)
            except Exception:
                pass


class DownloadService:
    """Handles downloading assets (avatars, splash arts, skill icons) and persisting metadata."""

    def __init__(self, scraper_service, timeout: int = 20, max_retries: int = 3):
        self.scraper = scraper_service
        self.session = requests.Session()
        self.timeout = timeout
        self.max_retries = max_retries

    def download_file(self, url: str, target_path: str, min_size: int = 100) -> bool:
        return safe_download_file(
            session=self.session,
            url=url,
            target_path=target_path,
            min_size=min_size,
            timeout=self.timeout,
            max_retries=self.max_retries
        )

    def download_hero(
        self,
        hero: dict,
        output_dir: str,
        image_types: list[str] = None,
        callback=None,
        cancel_check=None,
    ) -> dict:
        """Download requested assets for a single champion."""
        if image_types is None:
            image_types = ["avatar", "splash"]

        hero_name = hero.get("name", "Unknown")
        safe_hero_name = sanitize_filename(hero_name)
        hero_folder = os.path.join(output_dir, safe_hero_name)
        os.makedirs(hero_folder, exist_ok=True)

        results = {
            "hero": hero_name,
            "avatar": 0,
            "skins": 0,
            "skills": 0,
            "failed": 0
        }

        if cancel_check and cancel_check():
            return results

        # 1. Download Avatar
        if "avatar" in image_types and hero.get("avatar_url"):
            ext = os.path.splitext(urlparse(hero["avatar_url"]).path)[1] or ".jpg"
            avatar_path = os.path.join(hero_folder, f"avatar{ext}")
            ok = self.download_file(hero["avatar_url"], avatar_path)
            if ok:
                results["avatar"] += 1
            else:
                results["failed"] += 1
            _safe_callback(callback, hero_name, f"Avatar: {hero_name}", ok)

        if cancel_check and cancel_check():
            return results

        # 2. Fetch Detail if skins or skills needed
        need_detail = any(t in image_types for t in ["splash", "skills"])
        if need_detail and hero.get("url"):
            try:
                detail = self.scraper.get_hero_detail(hero["url"])

                # Download Skins
                if "splash" in image_types and detail.get("skins"):
                    skins_folder = os.path.join(hero_folder, "skins")
                    os.makedirs(skins_folder, exist_ok=True)
                    for idx, skin in enumerate(detail["skins"], start=1):
                        if cancel_check and cancel_check():
                            break
                        skin_name = skin.get("name") or f"Skin_{idx}"
                        safe_skin_name = sanitize_filename(skin_name)
                        img_url = skin.get("image_url") or skin.get("thumb_url")
                        if not img_url:
                            continue
                        ext = os.path.splitext(urlparse(img_url).path)[1] or ".jpg"
                        target_filename = f"{idx:02d}_{safe_skin_name}{ext}"
                        target_path = os.path.join(skins_folder, target_filename)
                        
                        ok = self.download_file(img_url, target_path)
                        if ok:
                            results["skins"] += 1
                        else:
                            results["failed"] += 1
                        _safe_callback(callback, hero_name, f"Trang phục: {skin_name}", ok)

                # Download Skills
                if "skills" in image_types and detail.get("skills"):
                    skills_folder = os.path.join(hero_folder, "skills")
                    os.makedirs(skills_folder, exist_ok=True)
                    for idx, skill in enumerate(detail["skills"], start=1):
                        if cancel_check and cancel_check():
                            break
                        skill_name = skill.get("name") or f"Kỹ_năng_{idx}"
                        safe_skill_name = sanitize_filename(skill_name)
                        icon_url = skill.get("icon_url")
                        if not icon_url:
                            continue
                        ext = os.path.splitext(urlparse(icon_url).path)[1] or ".png"
                        target_filename = f"{idx:02d}_{safe_skill_name}{ext}"
                        target_path = os.path.join(skills_folder, target_filename)

                        ok = self.download_file(icon_url, target_path)
                        if ok:
                            results["skills"] += 1
                        else:
                            results["failed"] += 1
                        _safe_callback(callback, hero_name, f"Kỹ năng: {skill_name}", ok)

                # Save complete hero metadata and skills to hero_info.json
                meta_path = os.path.join(hero_folder, "hero_info.json")
                hero_meta = {
                    "id": hero.get("id"),
                    "name": hero_name,
                    "url": hero.get("url"),
                    "avatar_url": hero.get("avatar_url"),
                    "roles": hero.get("roles", []),
                    "skins": detail.get("skins", []),
                    "skills": detail.get("skills", [])
                }
                try:
                    with open(meta_path, "w", encoding="utf-8") as f:
                        json.dump(hero_meta, f, ensure_ascii=False, indent=2)
                except Exception:
                    pass

            except Exception as e:
                results["error"] = str(e)
                _safe_callback(callback, hero_name, f"Lỗi chi tiết: {e}", False)

        _safe_callback(callback, hero_name, f"Hoàn thành {hero_name}", True, is_hero_finished=True)
        return results

    def download_heroes_batch(
        self,
        heroes: list[dict],
        output_dir: str,
        image_types: list[str] = None,
        max_workers: int = 5,
        callback=None,
        cancel_check=None,
    ) -> list[dict]:
        """Download multiple heroes in parallel using ThreadPoolExecutor."""
        results = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_hero = {
                executor.submit(
                    self.download_hero,
                    hero,
                    output_dir,
                    image_types,
                    callback,
                    cancel_check,
                ): hero
                for hero in heroes
            }
            for future in as_completed(future_to_hero):
                if cancel_check and cancel_check():
                    break
                try:
                    res = future.result()
                    results.append(res)
                except Exception as e:
                    h = future_to_hero[future]
                    results.append({"hero": h.get("name"), "error": str(e)})
        return results
