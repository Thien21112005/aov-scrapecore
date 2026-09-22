"""
Script đồng bộ dữ liệu kỹ năng từ AOV ScrapeCore sang AOV MetaForge (data.js).
Hỗ trợ:
- Cập nhật trực tiếp từ Garena cho 1 tướng cụ thể hoặc toàn bộ 129 tướng.
- Đồng bộ từ file JSON cục bộ (data/all_heroes_skills.json) sau khi bạn chỉnh sửa thủ công.
"""

import os
import sys
import json
import argparse
import re

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from scrapecore.services.scraper_service import ScraperService
from scrapecore.services.export_service import ExportService
from scrapecore.utils.text_utils import strip_accents

DEFAULT_SKILLS_JSON = os.path.join(os.path.dirname(__file__), "data", "all_heroes_skills.json")
DEFAULT_METAFORGE_DATA_JS = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "aov-metaforge", "js", "core", "data.js")
)


def update_data_js(metaforge_data_js: str, skills_dict: dict[str, list[dict]]) -> int:
    """Inject updated skills array into HEROES_DATABASE inside data.js."""
    if not os.path.exists(metaforge_data_js):
        print(f"[!] Không tìm thấy tệp data.js tại: {metaforge_data_js}")
        return 0

    with open(metaforge_data_js, "r", encoding="utf-8") as f:
        content = f.read()

    # Find the start of 'const HEROES_DATABASE = [' and its matching closing '];'
    start_match = re.search(r"const\s+HEROES_DATABASE\s*=\s*\[", content)
    if not start_match:
        print("[!] Không tìm thấy 'const HEROES_DATABASE =' trong data.js")
        return 0

    prefix = content[: start_match.start()]
    array_start_idx = start_match.end() - 1  # at the '['

    # Find the matching closing '];'
    end_match = re.search(r"\n\];\s*", content[array_start_idx:])
    if not end_match:
        print("[!] Không thể tìm thấy điểm kết thúc của HEROES_DATABASE")
        return 0

    array_end_idx = array_start_idx + end_match.start() + 2  # right after ']'
    suffix = content[array_start_idx + end_match.end() :]

    json_str = content[array_start_idx:array_end_idx]

    try:
        heroes_list = json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"[!] Lỗi phân tích cú pháp JSON trong data.js: {e}")
        return 0

    updated_count = 0
    for hero in heroes_list:
        hid = hero.get("id", "").lower()
        hname_norm = strip_accents(hero.get("name", "")).lower()

        matched_skills = None
        if hid in skills_dict:
            matched_skills = skills_dict[hid]
        else:
            for k, sk in skills_dict.items():
                if strip_accents(k).lower() == hname_norm:
                    matched_skills = sk
                    break

        if matched_skills:
            hero["skills"] = matched_skills
            updated_count += 1

    formatted_json = json.dumps(heroes_list, ensure_ascii=False, indent=2)
    new_content = f"{prefix}const HEROES_DATABASE = {formatted_json};\n\n{suffix}"

    with open(metaforge_data_js, "w", encoding="utf-8") as f:
        f.write(new_content)

    return updated_count


def main():
    parser = argparse.ArgumentParser(description="Đồng bộ dữ liệu kỹ năng sang AOV MetaForge")
    parser.add_argument("--hero", type=str, help="Cập nhật nhanh 1 tướng cụ thể từ Garena (VD: 'Tamyn', 'Florentino')")
    parser.add_argument("--all", action="store_true", help="Cào lại dữ liệu toàn bộ 129 tướng từ Garena và đồng bộ")
    parser.add_argument("--local", action="store_true", help="Chỉ đồng bộ từ file JSON cục bộ (data/all_heroes_skills.json) vào data.js")
    parser.add_argument("--target", type=str, default=DEFAULT_METAFORGE_DATA_JS, help="Đường dẫn file data.js của web")
    args = parser.parse_args()

    print("=" * 70)
    print("      AOV DATA SYNC — ĐỒNG BỘ DỮ LIỆU TƯỚNG VÀ CHIÊU THỨC")
    print("=" * 70)

    # Mode 1: Sync from local edited JSON
    if args.local:
        if not os.path.exists(DEFAULT_SKILLS_JSON):
            print(f"[!] Tệp {DEFAULT_SKILLS_JSON} không tồn tại.")
            return
        with open(DEFAULT_SKILLS_JSON, "r", encoding="utf-8") as f:
            local_data = json.load(f)
        skills_dict = {h["id"]: h.get("skills", []) for h in local_data if "id" in h}
        count = update_data_js(args.target, skills_dict)
        print(f"[✓] Đã đồng bộ {count} tướng từ tệp JSON cục bộ vào {args.target}")
        return

    scraper = ScraperService()

    # Mode 2: Update 1 single hero from live Garena
    if args.hero:
        print(f"[*] Đang tìm thông tin tướng '{args.hero}' trên Garena...")
        heroes = scraper.get_heroes()
        norm_target = strip_accents(args.hero).lower()
        matched = [
            h for h in heroes
            if norm_target == strip_accents(h["name"]).lower() or norm_target == h["id"].lower()
        ]
        if not matched:
            matched = [
                h for h in heroes
                if norm_target in strip_accents(h["name"]).lower() or norm_target in h["id"].lower()
            ]
        if not matched:
            print(f"[!] Không tìm thấy tướng nào khớp với '{args.hero}'.")
            return

        target_hero = matched[0]
        print(f"[*] Đang bóc tách chiêu thức mới nhất cho tướng: {target_hero['name']} ({target_hero['url']})...")
        detail = scraper.get_hero_detail(target_hero["url"])
        new_skills = detail.get("skills", [])

        # 1. Update in local all_heroes_skills.json
        if os.path.exists(DEFAULT_SKILLS_JSON):
            with open(DEFAULT_SKILLS_JSON, "r", encoding="utf-8") as f:
                all_json = json.load(f)
            found = False
            for item in all_json:
                if item.get("id") == target_hero["id"]:
                    item["skills"] = new_skills
                    found = True
                    break
            if not found:
                all_json.append({
                    "id": target_hero["id"],
                    "name": target_hero["name"],
                    "url": target_hero["url"],
                    "avatar_url": target_hero.get("avatar_url"),
                    "roles": target_hero.get("roles", []),
                    "skills": new_skills,
                    "skins_count": len(detail.get("skins", []))
                })
            with open(DEFAULT_SKILLS_JSON, "w", encoding="utf-8") as f:
                json.dump(all_json, f, ensure_ascii=False, indent=2)
            print(f"[✓] Đã cập nhật chiêu thức '{target_hero['name']}' vào {DEFAULT_SKILLS_JSON}")

        # 2. Inject into data.js
        skills_dict = {target_hero["id"]: new_skills}
        count = update_data_js(args.target, skills_dict)
        print(f"[✓] Đã đồng bộ chiêu thức mới của {target_hero['name']} vào web: {args.target}")
        return

    # Mode 3: Re-scrape all heroes and sync
    if args.all:
        print("[*] Đang cào lại toàn bộ kỹ năng của 129 tướng từ Garena...")
        exporter = ExportService(scraper)
        
        def _cb(hero_name, msg, ok):
            print(f"  -> {msg}")
            
        data = exporter.export_all_heroes_skills(DEFAULT_SKILLS_JSON, max_workers=10, callback=_cb)
        print(f"[✓] Đã xuất {len(data)} tướng vào {DEFAULT_SKILLS_JSON}")
        skills_dict = {h["id"]: h.get("skills", []) for h in data if "id" in h}
        count = update_data_js(args.target, skills_dict)
        print(f"[✓] Đã đồng bộ toàn bộ {count} tướng sang data.js thành công!")
        return

    # Default instructions
    print("Vui lòng chọn một tùy chọn:")
    print("  1. Cập nhật 1 tướng cụ thể:  python sync_metaforge.py --hero \"Tên_Tướng\"")
    print("  2. Cập nhật toàn bộ 129 tướng: python sync_metaforge.py --all")
    print("  3. Đồng bộ từ file JSON đã sửa: python sync_metaforge.py --local")


if __name__ == "__main__":
    main()
