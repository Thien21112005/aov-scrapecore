"""
Scraper Service: Handles HTTP requests, DOM extraction, and parsing from official Garena portal.
"""

import json
import time
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

from ..core.constants import BASE_URL, DEFAULT_HEADERS, ROLE_MAP, SKILL_TYPE_LABELS
from ..core.models import Champion, Skill, Skin
from ..utils.text_utils import clean_article_text


class ScraperService:
    """Scrapes champion lists, skin artwork, and detailed skill sets."""

    def __init__(self, timeout: int = 20, max_retries: int = 3, base_url: str = BASE_URL):
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        self.timeout = timeout
        self.max_retries = max_retries
        self.base_url = base_url
        self._cached_heroes = None

    def fetch_url(self, url: str) -> str:
        """Fetch HTML content with automatic retries."""
        for attempt in range(self.max_retries):
            try:
                resp = self.session.get(url, timeout=self.timeout)
                resp.raise_for_status()
                resp.encoding = 'utf-8'
                return resp.text
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise e
                time.sleep(1 + attempt)
        return ""

    def get_heroes(self, force_refresh: bool = False) -> list[dict]:
        """Fetch and parse indexed champions from the main portal listing."""
        if self._cached_heroes and not force_refresh:
            return self._cached_heroes

        html = self.fetch_url(self.base_url)
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

            # Extract roles
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

            if not detail_url.startswith("http"):
                detail_url = urljoin(self.base_url, detail_url)
            if avatar_url and not avatar_url.startswith("http"):
                avatar_url = urljoin(self.base_url, avatar_url)

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
        """Fetch champion detail page and parse skins and skills with full descriptions."""
        html = self.fetch_url(hero_url)
        soup = BeautifulSoup(html, "html.parser")

        # 1. Parse Skins
        skin_section = soup.find("section", class_="hero__skins")
        skins = []
        if skin_section:
            skin_detail_map = {}
            for detail_div in skin_section.select(".hero__skins--detail"):
                s_id = detail_div.get("id", "").strip()
                pic_img = detail_div.select_one("picture img")
                if not pic_img:
                    imgs = detail_div.find_all("img")
                    pic_img = next((i for i in imgs if "SkinLabel" not in i.get("src", "")), None)
                
                img_url = pic_img.get("src", "").strip() if pic_img else ""
                if img_url and not img_url.startswith("http"):
                    img_url = urljoin(hero_url, img_url)
                if s_id:
                    skin_detail_map[s_id] = img_url

            for a_tab in skin_section.select(".hero__skins--list a"):
                s_id = a_tab.get("href", "").replace("#", "").strip()
                skin_name = a_tab.get("title", "").strip() or a_tab.get_text(strip=True)

                thumb_img = a_tab.find("img")
                thumb_url = thumb_img.get("src", "").strip() if thumb_img else ""
                if thumb_url and not thumb_url.startswith("http"):
                    thumb_url = urljoin(hero_url, thumb_url)

                full_img_url = skin_detail_map.get(s_id, "") or thumb_url

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
            # Map id (e.g. heroSkill-1) -> {name, description}
            skill_details = {}
            for detail_div in skill_section.select(".hero__skills--detail"):
                s_id = detail_div.get("id", "").strip()
                h3 = detail_div.find("h3")
                skill_title = h3.get_text(strip=True) if h3 else ""
                article = detail_div.find("article")
                desc_text = clean_article_text(article)
                if s_id:
                    skill_details[s_id] = {
                        "name": skill_title,
                        "description": desc_text
                    }

            for idx, item in enumerate(skill_section.select(".hero__skills--list li a")):
                s_id = item.get("href", "").replace("#", "").strip()
                skill_name = item.get("title", "").strip()
                img_tag = item.find("img")
                if not skill_name and img_tag:
                    skill_name = img_tag.get("alt", "").strip()
                icon_url = img_tag.get("src", "").strip() if img_tag else ""
                if icon_url and not icon_url.startswith("http"):
                    icon_url = urljoin(hero_url, icon_url)

                detail_info = skill_details.get(s_id, {})
                final_name = detail_info.get("name") or skill_name or f"Chiêu_{idx+1}"
                final_desc = detail_info.get("description", "")
                skill_type = SKILL_TYPE_LABELS[idx] if idx < len(SKILL_TYPE_LABELS) else f"Kỹ năng {idx+1}"

                if icon_url or final_name:
                    skills.append({
                        "id": s_id or f"skill_{idx+1}",
                        "type": skill_type,
                        "name": final_name,
                        "icon_url": icon_url,
                        "description": final_desc
                    })

        return {"skins": skins, "skills": skills}
