"""
AOV ScrapeCore - Application Launcher
Entry point supporting CLI, interactive menu, and CustomTkinter Desktop GUI.
"""

import sys
from scrapecore.ui.cli.app import main as cli_main
from scrapecore.ui.gui.app import launch_gui


def main():
    if "--gui" in sys.argv:
        launch_gui()
    else:
        cli_main()


if __name__ == "__main__":
    main()
