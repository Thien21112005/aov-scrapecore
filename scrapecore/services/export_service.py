"""
Export Service: Exports crawled champion data and skills into normalized JSON schemas.
"""

import os
import json
from concurrent.futures import ThreadPoolExecutor, as_completed


class ExportService:
    """Exports datasets to structured JSON files."""

    def __init__(self, scraper_service):
        self.scraper = scraper_service

    def export_all_heroes_skills(
        self,
        output_file: str = "data/all_heroes_skills.json",
        max_workers: int = 10,
        callback=None,
    ) -> list[dict]:
        """Scrape complete skills and descriptions for all champions in parallel."""
        heroes = self.scraper.get_heroes()
        all_data = []

        def _fetch_one(hero):
            try:
                detail = self.scraper.get_hero_detail(hero["url"])
                return {
                    "id": hero.get("id"),
                    "name": hero.get("name"),
                    "url": hero.get("url"),
                    "avatar_url": hero.get("avatar_url"),
                    "roles": hero.get("roles", []),
                    "skills": detail.get("skills", []),
                    "skins_count": len(detail.get("skins", []))
                }
            except Exception as e:
                return {
                    "id": hero.get("id"),
                    "name": hero.get("name"),
                    "url": hero.get("url"),
                    "avatar_url": hero.get("avatar_url"),
                    "roles": hero.get("roles", []),
                    "skills": [],
                    "error": str(e)
                }

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_hero = {executor.submit(_fetch_one, h): h for h in heroes}
            for idx, future in enumerate(as_completed(future_to_hero), 1):
                res = future.result()
                all_data.append(res)
                if callback:
                    callback(res["name"], f"Đã cào {idx}/{len(heroes)}: {res['name']}", True)

        all_data.sort(key=lambda x: x.get("name", ""))

        os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)

        return all_data
