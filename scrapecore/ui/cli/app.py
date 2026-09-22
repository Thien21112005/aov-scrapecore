"""
Command-line interface (CLI) for Arena of Valor (Liên Quân Mobile) asset scraper and downloader.
"""

import os
import sys
import argparse

from ...services.scraper_service import ScraperService
from ...services.download_service import DownloadService
from ...services.export_service import ExportService
from ...utils.text_utils import strip_accents

# Ensure UTF-8 output on Windows terminal
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

try:
    from rich.console import Console
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
    HAS_RICH = True
    console = Console()
except ImportError:
    HAS_RICH = False
    console = None


def print_banner():
    banner_text = """
  ╔═══════════════════════════════════════════════════════════════════════╗
  ║       AOV SCRAPECORE - CHAMPION ASSET & METADATA SCRAPER             ║
  ║             Website: lienquan.garena.vn/hoc-vien/tuong-skin/          ║
  ╚═══════════════════════════════════════════════════════════════════════╝
"""
    if HAS_RICH:
        console.print(f"[bold cyan]{banner_text}[/bold cyan]")
    else:
        print(banner_text)


def parse_types(type_str: str) -> list[str]:
    """Parse comma-separated types or alias."""
    if not type_str or type_str == "all":
        return ["avatar", "splash", "skills"]
    types = [t.strip().lower() for t in type_str.split(",")]
    valid_types = []
    for t in types:
        if t in ["avatar", "ava"]:
            valid_types.append("avatar")
        elif t in ["splash", "skin", "skins"]:
            valid_types.append("splash")
        elif t in ["skills", "skill", "chieu"]:
            valid_types.append("skills")
    return valid_types or ["avatar", "splash"]


def display_heroes_table(heroes: list[dict]):
    """Display list of heroes in a formatted table."""
    if HAS_RICH:
        table = Table(title=f"Danh sách tướng Liên Quân ({len(heroes)} tướng)", show_lines=False)
        table.add_column("STT", justify="right", style="cyan", width=5)
        table.add_column("Tên tướng", style="bold green", min_width=15)
        table.add_column("Vai trò", style="yellow", min_width=15)
        table.add_column("Slug / ID", style="dim", min_width=15)

        for i, h in enumerate(heroes, 1):
            table.add_row(str(i), h["name"], ", ".join(h["roles"]), h["id"])
        console.print(table)
    else:
        print(f"\n--- DANH SÁCH TƯỚNG ({len(heroes)} tướng) ---")
        for i, h in enumerate(heroes, 1):
            roles = ", ".join(h["roles"])
            print(f"[{i:3d}] {h['name']:<18} | {roles:<15} ({h['id']})")


def run_download_with_progress(download_service: DownloadService, heroes: list[dict], output_dir: str, image_types: list[str], threads: int):
    """Execute download with progress indication."""
    total_heroes = len(heroes)
    if total_heroes == 0:
        print("[!] Không có tướng nào để tải.")
        return

    print(f"\n[*] Bắt đầu tải {total_heroes} tướng...")
    print(f"[*] Thư mục lưu: {os.path.abspath(output_dir)}")
    print(f"[*] Loại ảnh: {', '.join(image_types)} | Số luồng: {threads}\n")

    if HAS_RICH:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            task = progress.add_task(f"Đang tải {total_heroes} vị tướng...", total=total_heroes)

            def on_progress(hero_name, item_name, ok, is_finished=False):
                if is_finished:
                    progress.advance(task, 1)
                elif ok:
                    progress.update(task, description=f"[cyan]{hero_name}[/cyan] - {item_name}")

            results = download_service.download_heroes_batch(
                heroes,
                output_dir=output_dir,
                image_types=image_types,
                max_workers=threads,
                callback=on_progress
            )
            progress.update(task, description="[bold green]Hoàn tất tải về!")
    else:
        finished_count = 0
        def on_progress(hero_name, item_name, ok, is_finished=False):
            nonlocal finished_count
            if is_finished:
                finished_count += 1
                pct = (finished_count / total_heroes) * 100
                print(f"[{finished_count}/{total_heroes}] ({pct:.1f}%) Hoàn thành tướng: {hero_name}")
            elif not ok:
                print(f"  [x] Thất bại: {hero_name} - {item_name}")

        results = download_service.download_heroes_batch(
            heroes,
            output_dir=output_dir,
            image_types=image_types,
            max_workers=threads,
            callback=on_progress
        )

    # Summary
    total_avatar = sum(r.get("avatar", 0) for r in results)
    total_skins = sum(r.get("skins", 0) for r in results)
    total_skills = sum(r.get("skills", 0) for r in results)
    total_failed = sum(r.get("failed", 0) for r in results)

    print("\n" + "=" * 50)
    print("  KẾT QUẢ TẢI VỀ:")
    print(f"  - Số tướng đã xử lý: {len(results)}")
    print(f"  - Ảnh Avatar:       {total_avatar}")
    print(f"  - Ảnh Trang phục HD:{total_skins}")
    print(f"  - Ảnh Kỹ năng:      {total_skills}")
    if total_failed > 0:
        print(f"  - Tải lỗi:          {total_failed}")
    print(f"  - Lưu tại:          {os.path.abspath(output_dir)}")
    print("=" * 50 + "\n")


def interactive_menu(scraper: ScraperService, downloader: DownloadService, default_output: str = "downloads", default_threads: int = 5):
    """Interactive console menu for users."""
    print_banner()
    print("[*] Đang tải danh sách tướng từ website Liên Quân Mobile...")
    try:
        all_heroes = scraper.get_heroes()
        print(f"[✓] Đã tải danh sách {len(all_heroes)} tướng thành công!\n")
    except Exception as e:
        print(f"[!] Lỗi khi kết nối tới website: {e}")
        return

    while True:
        print("-" * 50)
        print("  CHỌN TÁC VỤ:")
        print("  [1] Tải ảnh TẤT CẢ các tướng (129+ tướng)")
        print("  [2] Tìm kiếm và tải theo Tên tướng (vd: Florentino, Valhein, Tulen...)")
        print("  [3] Tải theo Vai trò (Đấu sĩ, Xạ thủ, Pháp sư, Sát thủ, v.v.)")
        print("  [4] Xem danh sách tất cả các tướng")
        print("  [5] Xuất toàn bộ bộ kỹ năng 129 tướng ra JSON")
        print("  [6] Khởi chạy Giao diện đồ họa (GUI Desktop)")
        print("  [0] Thoát")
        print("-" * 50)

        choice = input("Nhập lựa chọn của bạn (0-6): ").strip()
        if choice == "0":
            print("Tạm biệt!")
            break
        elif choice == "6":
            from ..gui.app import launch_gui
            launch_gui()
            break
        elif choice == "5":
            out_file = input("Nhập tên file JSON lưu [mặc định: data/all_heroes_skills.json]: ").strip() or "data/all_heroes_skills.json"
            exporter = ExportService(scraper)
            print("[*] Đang cào dữ liệu kỹ năng...")
            data = exporter.export_all_heroes_skills(out_file, max_workers=default_threads, callback=lambda n, m, ok: print(f"  -> {m}"))
            print(f"[✓] Đã xuất thành công {len(data)} tướng ra: {out_file}")
            continue
        elif choice == "4":
            display_heroes_table(all_heroes)
            continue
        elif choice in ["1", "2", "3"]:
            target_heroes = []
            if choice == "1":
                target_heroes = all_heroes
            elif choice == "2":
                keyword = input("\nNhập tên tướng muốn tìm (không phân biệt dấu): ").strip()
                if not keyword:
                    print("[!] Tên không được để trống!")
                    continue
                norm_kw = strip_accents(keyword)
                target_heroes = [
                    h for h in all_heroes
                    if norm_kw in strip_accents(h["name"]) or norm_kw in strip_accents(h["id"])
                ]
                if not target_heroes:
                    print(f"[!] Không tìm thấy tướng nào khớp với '{keyword}'.")
                    continue
                print(f"[✓] Tìm thấy {len(target_heroes)} tướng: {', '.join(h['name'] for h in target_heroes)}")
            elif choice == "3":
                all_roles = set()
                for h in all_heroes:
                    all_roles.update(h["roles"])
                roles_list = sorted(list(all_roles))
                print("\nDanh sách vai trò:")
                for idx, r in enumerate(roles_list, 1):
                    print(f"  [{idx}] {r}")
                role_choice = input(f"Chọn vai trò (1-{len(roles_list)}): ").strip()
                try:
                    selected_role = roles_list[int(role_choice) - 1]
                except (ValueError, IndexError):
                    print("[!] Lựa chọn không hợp lệ.")
                    continue
                target_heroes = [h for h in all_heroes if selected_role in h["roles"]]
                print(f"[✓] Có {len(target_heroes)} tướng thuộc vai trò '{selected_role}'.")

            print("\nChọn loại ảnh cần tải:")
            print("  [1] Avatar + Trang phục HD (Khuyên dùng)")
            print("  [2] Chỉ tải Avatar (Ảnh đại diện)")
            print("  [3] Chỉ tải Trang phục HD (1920x1080 Splash Art)")
            print("  [4] Tất cả (Avatar + Trang phục HD + Chiêu thức kỹ năng)")
            type_choice = input("Lựa chọn (mặc định 1): ").strip() or "1"
            type_mapping = {
                "1": ["avatar", "splash"],
                "2": ["avatar"],
                "3": ["splash"],
                "4": ["avatar", "splash", "skills"],
            }
            img_types = type_mapping.get(type_choice, ["avatar", "splash"])

            out_folder = input(f"Thư mục lưu ảnh [mặc định: {default_output}]: ").strip() or default_output
            thread_input = input(f"Số luồng tải đồng thời [mặc định: {default_threads}]: ").strip()
            try:
                threads = int(thread_input) if thread_input else default_threads
            except ValueError:
                threads = default_threads

            run_download_with_progress(downloader, target_heroes, out_folder, img_types, threads)


def main():
    parser = argparse.ArgumentParser(
        description="AOV ScrapeCore - Tool cào và tải ảnh tướng, skin Liên Quân Mobile Full HD"
    )
    parser.add_argument("--all", action="store_true", help="Tải ảnh toàn bộ tất cả tướng")
    parser.add_argument("--hero", type=str, help="Tên vị tướng cần tải (ví dụ: Florentino, Valhein, Qi)")
    parser.add_argument("--role", type=str, help="Tải theo vai trò (Xạ thủ, Đấu sĩ, Pháp sư, Sát thủ, Trợ thủ, Đỡ đòn)")
    parser.add_argument(
        "--type",
        type=str,
        default="avatar,splash",
        help="Loại ảnh tải về: avatar, splash, skills hoặc all (mặc định: avatar,splash)"
    )
    parser.add_argument("--output", "-o", type=str, default="downloads", help="Thư mục lưu ảnh (mặc định: downloads)")
    parser.add_argument("--threads", "-t", type=int, default=5, help="Số luồng tải đa luồng đồng thời (mặc định: 5)")
    parser.add_argument("--list", action="store_true", help="Hiển thị danh sách tất cả các tướng")
    parser.add_argument("--export-skills", type=str, nargs="?", const="data/all_heroes_skills.json", help="Cào và xuất toàn bộ kỹ năng & mô tả của 129 tướng ra file JSON")
    parser.add_argument("--gui", action="store_true", help="Khởi chạy giao diện đồ họa (GUI Desktop)")

    args = parser.parse_args()

    scraper = ScraperService()
    downloader = DownloadService(scraper)
    exporter = ExportService(scraper)

    if args.gui:
        from ..gui.app import launch_gui
        launch_gui()
        return

    if args.export_skills:
        print_banner()
        output_file = args.export_skills
        print(f"[*] Đang cào dữ liệu toàn bộ kỹ năng & mô tả của 129 tướng...")
        print(f"[*] File đích: {output_file}")
        
        def _cb(hero_name, msg, ok):
            print(f"  -> {msg}")
            
        data = exporter.export_all_heroes_skills(output_file, max_workers=args.threads, callback=_cb)
        print(f"\n[✓] Thành công! Đã cào và lưu thông tin kỹ năng của {len(data)} tướng vào: {output_file}")
        return

    if args.list:
        print_banner()
        heroes = scraper.get_heroes()
        display_heroes_table(heroes)
        return

    image_types = parse_types(args.type)

    if args.all:
        print_banner()
        heroes = scraper.get_heroes()
        run_download_with_progress(downloader, heroes, args.output, image_types, args.threads)
        return

    if args.hero:
        print_banner()
        heroes = scraper.get_heroes()
        norm_kw = strip_accents(args.hero)
        matched = [
            h for h in heroes
            if norm_kw in strip_accents(h["name"]) or norm_kw in strip_accents(h["id"])
        ]
        if not matched:
            print(f"[!] Không tìm thấy tướng nào khớp với tên: '{args.hero}'")
            return
        run_download_with_progress(downloader, matched, args.output, image_types, args.threads)
        return

    if args.role:
        print_banner()
        heroes = scraper.get_heroes()
        norm_role = strip_accents(args.role)
        matched = [
            h for h in heroes
            if any(norm_role in strip_accents(r) for r in h["roles"])
        ]
        if not matched:
            print(f"[!] Không tìm thấy tướng nào thuộc vai trò: '{args.role}'")
            return
        run_download_with_progress(downloader, matched, args.output, image_types, args.threads)
        return

    interactive_menu(scraper, downloader, default_output=args.output, default_threads=args.threads)


if __name__ == "__main__":
    main()
