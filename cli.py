"""
CLI Entry Point Proxy (Compatibility Layer)
Delegates to modular scrapecore.ui.cli.app.
"""

from scrapecore.ui.cli.app import main

if __name__ == "__main__":
    main()
