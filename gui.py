"""
GUI Entry Point Proxy (Compatibility Layer)
Delegates to modular scrapecore.ui.gui.app.
"""

from scrapecore.ui.gui.app import launch_gui

if __name__ == "__main__":
    launch_gui()
