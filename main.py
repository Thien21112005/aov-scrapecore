"""
Main entry point for Lien Quan Mobile Champion & Skin Downloader.
Can run both Modern GUI mode and CLI mode.
"""

import sys
import os

# Ensure project directory is in python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    # If any CLI arguments are provided (e.g. --all, --hero, --role, --list, --threads, etc.)
    cli_flags = {"--all", "--hero", "--role", "--type", "--output", "-o", "--threads", "-t", "--list", "--cli"}
    has_cli_flag = any(arg in cli_flags for arg in sys.argv[1:])

    if has_cli_flag:
        from cli import main as run_cli
        run_cli()
        return

    # Check if user specifically requested --gui or no args
    if "--gui" in sys.argv:
        from gui import launch_gui
        launch_gui()
        return

    # If no arguments given, default to launching GUI, falling back to CLI if headless
    try:
        from gui import launch_gui
        launch_gui()
    except Exception as e:
        print(f"[*] Không thể khởi động GUI ({e}). Chuyển sang chế độ dòng lệnh CLI...")
        from cli import main as run_cli
        run_cli()


if __name__ == "__main__":
    main()
