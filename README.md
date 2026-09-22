# AOV ScrapeCore

> High-performance asset & metadata scraper for Arena of Valor (Liên Quân Mobile).

[English](README.md) | [Tiếng Việt](README.vi.md)

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Architecture: Layered](https://img.shields.io/badge/architecture-layered%20clean-emerald.svg)](https://en.wikipedia.org/wiki/Multitier_architecture)

A high-performance scraping engine and downloader designed to extract comprehensive metadata, high-resolution splash art, avatars, skill sets, and balance descriptions for all champions in Arena of Valor (Liên Quân Mobile) directly from official Garena portals.

---

## Architectural Design

`aov-scrapecore` is engineered following a modular, 3-tier layered architecture (Domain, Services, Utilities, and Presentation) ensuring separation of concerns, testability, and maintainability.

```text
aov-scrapecore/
├── scrapecore/
│   ├── core/                  # Domain Layer: Entities, data classes & global constants
│   │   ├── constants.py       # Base URLs, headers, and role mappings
│   │   └── models.py          # Champion, Skill, Skin, and DownloadResult dataclasses
│   │
│   ├── services/              # Application / Business Logic Layer
│   │   ├── scraper_service.py # HTML fetching, DOM parsing, and skill extraction
│   │   ├── download_service.py# Multi-threaded asset downloader & progress tracking
│   │   └── export_service.py  # JSON normalization and dataset exporter
│   │
│   ├── utils/                 # Infrastructure / Utility Layer
│   │   ├── file_utils.py      # Cross-platform path sanitization and atomic file I/O
│   │   └── text_utils.py      # Unicode NFD normalization and accent stripping
│   │
│   └── ui/                    # Presentation / Interface Layer
│       ├── cli/               # Command-line interface and interactive menu
│       │   └── app.py
│       └── gui/               # CustomTkinter dark-themed desktop application
│           └── app.py
│
├── main.py                    # Application entrypoint (CLI or GUI router)
├── cli.py                     # Backward-compatible CLI proxy
├── gui.py                     # Backward-compatible GUI proxy
├── scraper.py                 # Backward-compatible Scraper API proxy
├── data/
│   └── all_heroes_skills.json # Full dataset of all 129 champions and skills
├── requirements.txt           # Production dependencies
├── run_cli.bat                # Windows 1-click CLI launcher
├── run_gui.bat                # Windows 1-click GUI launcher
└── LICENSE                    # MIT License
```

---

## Key Capabilities

- **Complete Champion Indexing**: Indexes all 129+ champions including newly added heroes (Tamyn, Charlotte, Flowborn, etc.).
- **Skill Extraction with Deep Text Mining**: Parses passive and active skills, extracting numerical damage formulas, scaling rates, cooldowns, and mechanics from detail articles.
- **Concurrent Asset Downloader**: Multi-threaded request pooling (`ThreadPoolExecutor`) with automatic retry logic, rate-limit throttling, and skip-if-cached verification.
- **Dual User Interface**:
  - **Desktop GUI**: Built with CustomTkinter featuring multi-select, role filtering, search, and real-time logs.
  - **CLI & Automation**: Argument-driven command-line utility with rich terminal formatting and batch scraping.
- **Structured JSON Exports**: Normalizes data ready for downstream databases, game simulators, or web frontends.

---

## Installation

### Prerequisites
- Python 3.10 or higher
- Git

### Setup
```bash
git clone https://github.com/Thien21112005/aov-scrapecore.git
cd aov-scrapecore

# Create virtual environment
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## Usage Guide

### 1. Desktop Graphical Interface (GUI)
```bash
python main.py --gui
# or run_gui.bat on Windows
```

### 2. Command-Line Interface (CLI)

#### Interactive Menu
```bash
python main.py
# or python cli.py
```

#### Command Arguments
```bash
# Download assets for a specific champion
python cli.py --hero "Florentino"
python cli.py --hero "Tamyn"

# Filter by role
python cli.py --role "Xạ thủ"
python cli.py --role "Đấu sĩ"

# Download all champions
python cli.py --all

# Specify asset types: avatar, splash, skills, or all (default: avatar,splash)
python cli.py --hero "Valhein" --type all

# Export full 129 champions skills dataset to JSON
python cli.py --export-skills data/all_heroes_skills.json

# Adjust output path and concurrent thread workers
python cli.py --all --output "D:/Assets/AOV" --threads 8

# List all indexed champions
python cli.py --list
```

### 3. Python SDK / Programmatic Integration

```python
from scrapecore.services.scraper_service import ScraperService
from scrapecore.services.download_service import DownloadService
from scrapecore.services.export_service import ExportService

scraper = ScraperService(timeout=20)
downloader = DownloadService(scraper)
exporter = ExportService(scraper)

# 1. Fetch all champions list
heroes = scraper.get_heroes()
print(f"Total champions: {len(heroes)}")

# 2. Extract detailed skills for a champion
hero_url = "https://lienquan.garena.vn/hoc-vien/tuong-skin/d/tamyn/"
detail = scraper.get_hero_detail(hero_url)
for skill in detail["skills"]:
    print(f"[{skill['type']}] {skill['name']}: {skill['description'][:60]}...")

# 3. Batch export dataset
exporter.export_all_heroes_skills("data/all_heroes_skills.json", max_workers=10)
```

---

## Output Data Schema

Example `hero_info.json`:
```json
{
  "id": "tamyn",
  "name": "Tamyn",
  "url": "https://lienquan.garena.vn/hoc-vien/tuong-skin/d/tamyn/",
  "avatar_url": "https://lienquan.garena.vn/wp-content/uploads/...",
  "roles": ["Đấu sĩ"],
  "skills": [
    {
      "id": "heroSkill-1",
      "type": "Nội tại",
      "name": "Thánh Thương Quang Minh",
      "icon_url": "https://lienquan.garena.vn/wp-content/uploads/...png",
      "description": "Sau khi nhặt đoản thương, đòn đánh thường của Tamyn sẽ được cường hóa..."
    }
  ]
}
```

---

## License & Disclaimer

Distributed under the [MIT License](LICENSE).

All game artwork, champion assets, and descriptions are intellectual property of **Tencent Games** and **Garena**. This repository is intended strictly for personal research, educational analysis, and community utility integration.
