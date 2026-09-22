"""
Scraper module for Lien Quan Mobile champions, skins, and skills images.
Website: https://lienquan.garena.vn/hoc-vien/tuong-skin/
"""

import os
import re
import json
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse, urljoin
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://lienquan.garena.vn/hoc-vien/tuong-skin/"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "vi,en-US;q=0.9,en;q=0.8",
}

ROLE_MAP = {
    28: "Đấu sĩ",
    31: "Đỡ đòn",
    29: "Pháp sư",
    32: "Sát thủ",
    30: "Trợ thủ",
    33: "Xạ thủ",
}


def sanitize_filename(name: str) -> str:
    """Sanitize string to be safe for Windows file and folder names."""
    if not name:
        return "unnamed"
    # Replace illegal Windows characters: < > : " / \ | ? *
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    # Remove leading/trailing spaces and dots
    name = name.strip(' .')
    # Collapse multiple spaces or underscores
    name = re.sub(r'\s+', ' ', name)
    return name or "unnamed"


def strip_accents(text: str) -> str:
    """Convert accented Vietnamese text to plain ASCII for easy searching."""
    if not text:
        return ""
    text = unicodedata.normalize('NFD', text)
    text = re.sub(r'[\u0300-\u036f]', '', text)
    text = text.replace('đ', 'd').replace('Đ', 'D')
    return text.lower()


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


class AOVScraper:
    def __init__(self, timeout: int = 20, max_retries: int = 3):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.timeout = timeout
        self.max_retries = max_retries
        self._cached_heroes = None

    def fetch_url(self, url: str) -> str:
        """Fetch HTML content with automatic retries."""
        for attempt in range(self.max_retries):
            try:
                resp = self.session.get(url, timeout=self.timeout)
                resp.raise_for_status()
                # Ensure proper UTF-8 decoding
                resp.encoding = 'utf-8'
                return resp.text
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise e
                time.sleep(1 + attempt)
        return ""

    def get_heroes(self, force_refresh: bool = False) -> list[dict]:
        """
        Fetch and parse list of all champions from main listing page.
        Returns list of dicts:
        [
            {
                "id": str,
                "name": str,
                "url": str,
                "avatar_url": str,
                "roles": [str, ...]
            },
            ...
        ]
        """
        if self._cached_heroes and not force_refresh:
            return self._cached_heroes

        html = self.fetch_url(BASE_URL)
        soup = BeautifulSoup(html, "html.parser")

        # Parse role mapping if dynamically present
        role_map = dict(ROLE_MAP)
        role_items = soup.select(".st-heroes__types li a")
        for r in role_items:
            try:
                r_id = int(r.get("data-id", 0))
                r_name = r.get_text(strip=True)
                if r_id and r_name:
                    role_map[r_id] = r_name
            except (ValueError, TypeError):
                continue

        hero_items = soup.select(".st-heroes__list .st-heroes__item")
        heroes = []

        for item in hero_items:
            detail_url = item.get("href", "").strip()
            name_tag = item.select_one(".st-heroes__item--name")
            name = name_tag.get_text(strip=True) if name_tag else ""
            
            img_tag = item.select_one(".st-heroes__item--img img")
            avatar_url = img_tag.get("src", "").strip() if img_tag else ""

            # Roles from data-type="[28]"
            data_type = item.get("data-type", "[]")
            roles = []
            try:
                type_ids = json.loads(data_type)
                if isinstance(type_ids, list):
                    roles = [role_map.get(t_id, f"Vai trò {t_id}") for t_id in type_ids if t_id in role_map]
            except Exception:
                pass

            if not roles:
                roles = ["Khác"]

            if not name or not detail_url:
                continue

            # Ensure valid full URL
            if not detail_url.startswith("http"):
                detail_url = urljoin(BASE_URL, detail_url)
            if avatar_url and not avatar_url.startswith("http"):
                avatar_url = urljoin(BASE_URL, avatar_url)

            # Generate unique identifier
            slug = detail_url.rstrip("/").split("/")[-1]
            hero_info = {
                "id": slug,
                "name": name,
                "url": detail_url,
                "avatar_url": avatar_url,
                "roles": roles,
            }
            heroes.append(hero_info)

        self._cached_heroes = heroes
        return heroes

    def get_hero_detail(self, hero_url: str) -> dict:
        """
        Fetch a champion detail page and parse skins and skills.
        """
        html = self.fetch_url(hero_url)
        soup = BeautifulSoup(html, "html.parser")

        # 1. Parse Skins
        skin_section = soup.find("section", class_="hero__skins")
        skins = []
        if skin_section:
            # Map skin id (e.g. heroSkin-1) -> full image url
            skin_detail_map = {}
            for detail_div in skin_section.select(".hero__skins--detail"):
                s_id = detail_div.get("id", "").strip()
                # Find full artwork inside <picture><img src="..."> or directly <img>
                pic_img = detail_div.select_one("picture img")
                if not pic_img:
                    imgs = detail_div.find_all("img")
                    pic_img = next((i for i in imgs if "SkinLabel" not in i.get("src", "")), None)
                
                img_url = pic_img.get("src", "").strip() if pic_img else ""
                if img_url and not img_url.startswith("http"):
                    img_url = urljoin(hero_url, img_url)
                if s_id:
                    skin_detail_map[s_id] = img_url

            # Parse skin titles from tabs
            for a_tab in skin_section.select(".hero__skins--list a"):
                s_id = a_tab.get("href", "").replace("#", "").strip()
                skin_name = a_tab.get("title", "").strip()
                if not skin_name:
                    skin_name = a_tab.get_text(strip=True)

                thumb_img = a_tab.find("img")
                thumb_url = thumb_img.get("src", "").strip() if thumb_img else ""
                if thumb_url and not thumb_url.startswith("http"):
                    thumb_url = urljoin(hero_url, thumb_url)

                full_img_url = skin_detail_map.get(s_id, "")
                if not full_img_url and thumb_url:
                    full_img_url = thumb_url

                if full_img_url or thumb_url:
                    skins.append({
                        "id": s_id,
                        "name": skin_name or f"Skin_{len(skins)+1}",
                        "image_url": full_img_url,
                        "thumb_url": thumb_url
                    })

        # 2. Parse Skills
        skill_section = soup.find("section", class_="hero__skills")
        skills = []
        if skill_section:
            for item in skill_section.select(".hero__skills--list li a"):
                skill_name = item.get("title", "").strip()
                img_tag = item.find("img")
                if not skill_name and img_tag:
                    skill_name = img_tag.get("alt", "").strip()
                icon_url = img_tag.get("src", "").strip() if img_tag else ""
                if icon_url and not icon_url.startswith("http"):
                    icon_url = urljoin(hero_url, icon_url)

                if icon_url:
                    skills.append({
                        "name": skill_name or f"Chiêu_{len(skills)+1}",
                        "icon_url": icon_url
                    })

        return {"skins": skins, "skills": skills}

    def download_file(self, url: str, target_path: str, min_size: int = 100) -> bool:
        """
        Download a file safely with streaming.
        Skips if file already exists and is valid size.
        """
        if not url:
            return False

        if os.path.exists(target_path) and os.path.getsize(target_path) > min_size:
            return True  # Already downloaded

        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        temp_path = f"{target_path}.tmp"

        for attempt in range(self.max_retries):
            try:
                resp = self.session.get(url, stream=True, timeout=self.timeout)
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
                if attempt == self.max_retries - 1:
                    return False
                time.sleep(1)
        return False

    def download_hero(
        self,
        hero: dict,
        output_dir: str,
        image_types: list[str] = None,
        callback=None,
        cancel_check=None,
    ) -> dict:
        """
        Download all requested images for a single champion.
        """
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
                detail = self.get_hero_detail(hero["url"])

                # Download Skins / Splash art
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
        """
        Download multiple heroes in parallel using ThreadPoolExecutor.
        """
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

