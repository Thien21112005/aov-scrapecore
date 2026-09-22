"""
Scraper Module Proxy (Compatibility Layer)
Exposes ScraperService, DownloadService, and utilities under their historical names.
"""

from scrapecore.services.scraper_service import ScraperService
from scrapecore.services.download_service import DownloadService
from scrapecore.services.export_service import ExportService
from scrapecore.utils.file_utils import sanitize_filename, safe_download_file
from scrapecore.utils.text_utils import strip_accents
from scrapecore.core.constants import BASE_URL, DEFAULT_HEADERS as HEADERS, ROLE_MAP


class AOVScraper:
    """Backward compatibility wrapper unifying scraping and downloading."""

    def __init__(self, timeout: int = 20, max_retries: int = 3):
        self.scraper_service = ScraperService(timeout=timeout, max_retries=max_retries)
        self.download_service = DownloadService(self.scraper_service, timeout=timeout, max_retries=max_retries)
        self.export_service = ExportService(self.scraper_service)

    def fetch_url(self, url: str) -> str:
        return self.scraper_service.fetch_url(url)

    def get_heroes(self, force_refresh: bool = False) -> list[dict]:
        return self.scraper_service.get_heroes(force_refresh=force_refresh)

    def get_hero_detail(self, hero_url: str) -> dict:
        return self.scraper_service.get_hero_detail(hero_url)

    def download_file(self, url: str, target_path: str, min_size: int = 100) -> bool:
        return self.download_service.download_file(url, target_path, min_size=min_size)

    def download_hero(
        self,
        hero: dict,
        output_dir: str,
        image_types: list[str] = None,
        callback=None,
        cancel_check=None,
    ) -> dict:
        return self.download_service.download_hero(
            hero=hero,
            output_dir=output_dir,
            image_types=image_types,
            callback=callback,
            cancel_check=cancel_check
        )

    def download_heroes_batch(
        self,
        heroes: list[dict],
        output_dir: str,
        image_types: list[str] = None,
        max_workers: int = 5,
        callback=None,
        cancel_check=None,
    ) -> list[dict]:
        return self.download_service.download_heroes_batch(
            heroes=heroes,
            output_dir=output_dir,
            image_types=image_types,
            max_workers=max_workers,
            callback=callback,
            cancel_check=cancel_check
        )

    def export_all_heroes_skills(
        self,
        output_file: str = "data/all_heroes_skills.json",
        max_workers: int = 10,
        callback=None,
    ) -> list[dict]:
        return self.export_service.export_all_heroes_skills(
            output_file=output_file,
            max_workers=max_workers,
            callback=callback
        )
