# AOV ScrapeCore

> High-performance asset & metadata scraper for Arena of Valor (Liên Quân Mobile).

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A high-performance scraping engine and downloader designed to extract comprehensive metadata, high-resolution splash art, avatars, skill sets, and balance descriptions for all champions in Arena of Valor (Liên Quân Mobile) directly from official Garena portals.

---

## Features

- **Comprehensive Champion Coverage**: Automated indexing of all 129+ champions, including newly released heroes (Tamyn, Flowborn, Charlotte, etc.).
- **Rich Skill Set & Description Mining**: Parses passive and active skills with full numerical formulas, cooldowns, and mechanics from detail articles.
- **High-Resolution Asset Extraction**: Downloads uncompressed avatars, splash arts (1080p+), and skill icons directly from CDN endpoints.
- **Dual Interface**:
  - **Modern Desktop GUI**: CustomTkinter-based interface with search, role filters, real-time download logs, and progress indicators.
  - **CLI & Automation API**: Argument-driven command-line utility with rich terminal formatting and batch scraping.
- **Concurrent Engine**: Multi-threaded request pooling (`ThreadPoolExecutor`) with automatic retry logic, rate-limit throttling, and skip-if-cached verification.
- **Structured Data Export**: Outputs normalized JSON schemas ready for downstream databases, simulators, and mobile/web applications.

---

## Directory Structure

```text
aov-scrapecore/
├── cli.py                  # Command-line interface and interactive menu
├── gui.py                  # CustomTkinter desktop graphical interface
├── main.py                 # Application launcher
├── scraper.py              # Core scraping engine and network clients
├── requirements.txt        # Runtime dependencies
├── run_cli.bat             # Windows CLI launcher script
├── run_gui.bat             # Windows GUI launcher script
├── data/                   # Seed and exported JSON datasets
└── downloads/              # Downloaded champion assets (git-ignored)
    └── <Champion_Name>/
        ├── avatar.jpg
        ├── hero_info.json  # Champion metadata and complete skill set
        ├── skins/          # High-resolution splash arts
        └── skills/         # Skill icons
```

---

## Installation

### Prerequisites
- Python 3.10 or higher
- Git

### Setup
```bash
# Clone the repository
git clone https://github.com/Thien21112005/aov-scrapecore.git
cd aov-scrapecore

# Create and activate virtual environment (optional but recommended)
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

### 1. Graphical User Interface (GUI)

Launch the desktop interface:
```bash
python main.py --gui
# or double click run_gui.bat on Windows
```

### 2. Command-Line Interface (CLI)

#### Interactive Menu
```bash
python cli.py
# or double click run_cli.bat on Windows
```

#### Command Arguments
```bash
# Download assets for a specific champion
python cli.py --hero "Florentino"
python cli.py --hero "Tamyn"

# Download champions filtered by role
python cli.py --role "Xạ thủ"
python cli.py --role "Đấu sĩ"

# Download all champions (129+ heroes)
python cli.py --all

# Specify asset types: avatar, splash, skills, or all (default: avatar,splash)
python cli.py --hero "Valhein" --type all

# Export complete champion skills dataset to JSON
python cli.py --export-skills data/all_heroes_skills.json

# Adjust output path and concurrent thread workers
python cli.py --all --output "D:/Assets/AOV" --threads 8

# List all available champions
python cli.py --list
```

### 3. Python API Integration

```python
from scraper import AOVScraper

scraper = AOVScraper(timeout=20, max_retries=3)

# 1. Fetch all champions list
heroes = scraper.get_heroes()
print(f"Total indexed champions: {len(heroes)}")

# 2. Extract detail metadata and skills for a champion
hero_url = "https://lienquan.garena.vn/hoc-vien/tuong-skin/d/tamyn/"
detail = scraper.get_hero_detail(hero_url)

for skill in detail["skills"]:
    print(f"[{skill['type']}] {skill['name']}: {skill['description'][:60]}...")

# 3. Download assets for a hero
results = scraper.download_hero(
    hero=heroes[0],
    output_dir="downloads",
    image_types=["avatar", "splash", "skills"]
)
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
      "description": "Sau khi nhặt đoản thương, đòn đánh thường của Tamyn sẽ được cường hóa trong 4 giây..."
    },
    {
      "id": "heroSkill-2",
      "type": "Chiêu 1",
      "name": "Thương Phá Tầng Không",
      "icon_url": "https://lienquan.garena.vn/wp-content/uploads/...png",
      "description": "Tamyn phóng đoản thương theo hướng chỉ định, gây sát thương vật lý..."
    }
  ]
}
```

---

## Configuration & Rate Limiting

- Network requests run through a pooled `requests.Session` with custom User-Agent headers.
- Automatic exponential backoff prevents IP rate-limiting from CDN edge servers.
- Safe Windows path sanitization is applied to all filenames and directory paths.

---

## Contributing

Pull requests and issues are welcome. For major architectural changes, please open an issue first to discuss your proposal.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/new-capability`)
3. Commit your changes (`git commit -m 'feat: add new capability'`)
4. Push to the branch (`git push origin feature/new-capability`)
5. Open a Pull Request

---

## License

Distributed under the [MIT License](LICENSE).

All game artwork, champion assets, and descriptions are intellectual property of **Tencent Games** and **Garena**. This repository is intended strictly for personal research, educational analysis, and community utility integration.
