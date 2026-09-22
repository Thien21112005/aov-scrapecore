# AOV ScrapeCore

> High-performance asset & metadata scraper for Arena of Valor (Liên Quân Mobile).

<p align="left">
  <strong>Language / Ngôn ngữ:</strong>
  <a href="#english">English</a> &bull;
  <a href="#tiếng-việt">Tiếng Việt</a>
</p>

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Architecture: Layered](https://img.shields.io/badge/architecture-layered%20clean-emerald.svg)](https://en.wikipedia.org/wiki/Multitier_architecture)

---

<div id="english"></div>

## English

A high-performance scraping engine and asset downloader designed to extract comprehensive metadata, high-resolution splash art, avatars, skill sets, and balance descriptions for all champions in Arena of Valor (Liên Quân Mobile) directly from official Garena portals.

### Table of Contents
- [Architectural Design](#architectural-design)
- [Key Capabilities](#key-capabilities)
- [Installation](#installation)
- [Usage Guide](#usage-guide)
  - [1. Desktop Graphical Interface (GUI)](#1-desktop-graphical-interface-gui)
  - [2. Command-Line Interface (CLI)](#2-command-line-interface-cli)
  - [3. Python SDK / Programmatic Integration](#3-python-sdk--programmatic-integration)
- [Data Refresh & Balance Updates Guide](#data-refresh--balance-updates-guide)
- [Output Data Schema](#output-data-schema)
- [License & Disclaimer](#license--disclaimer)

---

### Architectural Design

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

### Key Capabilities

- **Complete Champion Indexing**: Indexes all 129+ champions including newly added heroes (Tamyn, Charlotte, Flowborn, etc.).
- **Skill Extraction with Deep Text Mining**: Parses passive and active skills, extracting numerical damage formulas, scaling rates, cooldowns, and mechanics from detail articles.
- **Concurrent Asset Downloader**: Multi-threaded request pooling (`ThreadPoolExecutor`) with automatic retry logic, rate-limit throttling, and skip-if-cached verification.
- **Dual User Interface**:
  - **Desktop GUI**: Built with CustomTkinter featuring multi-select, role filtering, search, and real-time logs.
  - **CLI & Automation**: Argument-driven command-line utility with rich terminal formatting and batch scraping.
- **Structured JSON Exports**: Normalizes data ready for downstream databases, game simulators, or web frontends.

---

### Installation

#### Prerequisites
- Python 3.10 or higher
- Git

#### Setup
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

### Usage Guide

#### 1. Desktop Graphical Interface (GUI)
```bash
python main.py --gui
# or run_gui.bat on Windows
```

#### 2. Command-Line Interface (CLI)

##### Interactive Menu
```bash
python main.py
# or python cli.py
```

##### Command Arguments
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

# Update a single champion's skills live from Garena and sync to web
python cli.py --update-skills "Tamyn"

# Synchronize local skills JSON to AOV MetaForge web (data.js)
python cli.py --sync-metaforge

# Adjust output path and concurrent thread workers
python cli.py --all --output "D:/Assets/AOV" --threads 8

# List all indexed champions
python cli.py --list
```

#### 3. Python SDK / Programmatic Integration

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

### Data Refresh & Balance Updates Guide

When champions receive balance changes (buffs, nerfs, reworks) or when new heroes are released, you can refresh or customize the data using four convenient workflows:

#### Workflow 1: Fast Single-Hero Live Update (Recommended for Patches)
To update skill descriptions, damage formulas, and cooldowns for a specific hero directly from Garena:
```bash
python cli.py --update-skills "Tamyn"
# or
python sync_metaforge.py --hero "Florentino"
```
*Effect: Automatically crawls the latest data from Garena, saves it to `data/all_heroes_skills.json`, and immediately synchronizes it into `aov-metaforge/js/core/data.js`.*

#### Workflow 2: Full Season / Big Patch Refresh (All 129 Champions)
When a new season starts or a massive balance patch drops:
```bash
python sync_metaforge.py --all
```
*Effect: Crawls all 129 champions from Garena in parallel and refreshes both local JSON and the companion web app.*

#### Workflow 3: Manual Stats & Balance Tuning (Custom Numbers)
If Garena hasn't updated their web portal yet or you wish to test custom damage numbers:
1. Open `data/all_heroes_skills.json`.
2. Locate the champion (e.g., search for `"Tamyn"`).
3. Directly edit the damage values, scaling ratios, or skill mechanics in the `"description"` field.
4. Push your manual edits into the web app with:
```bash
python cli.py --sync-metaforge
```

#### Workflow 4: Tactical Meta Stats Tuning (Tier, Mobility, CC Rating)
Advanced tactical ratings for the web app are maintained in `aov-metaforge/js/core/data.js`:
- `"tier"`: `"S+"`, `"S"`, `"A"`, `"B"`
- `"mobility"`: Integer score (0 - 100)
- `"cc_rating"`: Integer score (0 - 100)
- `"countered_by"`, `"counters"`, `"synergies"`: Lists of champion IDs.
Edit these fields directly in `data.js` to immediately update live tier lists, lane recommendations, and modal meters.

---

### Output Data Schema

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

### License & Disclaimer

Distributed under the [MIT License](LICENSE).

All game artwork, champion assets, and descriptions are intellectual property of **Tencent Games** and **Garena**. This repository is intended strictly for personal research, educational analysis, and community utility integration.

<p align="right"><a href="#aov-scrapecore">Back to Top</a> &bull; <a href="#tiếng-việt">Chuyển sang Tiếng Việt</a></p>

---

<div id="tiếng-việt"></div>
<div id="tieng-viet"></div>

## Tiếng Việt

> Công cụ cào và trích xuất tài nguyên, kỹ năng tướng Liên Quân Mobile (Arena of Valor) hiệu năng cao.

Engine cào dữ liệu và tải xuống tài nguyên được thiết kế chuyên sâu để trích xuất siêu dữ liệu, hình nền trang phục Full HD (1920x1080), ảnh đại diện avatar, bộ chiêu thức và nội dung mô tả chỉ số cơ chế của toàn bộ các vị tướng Liên Quân Mobile từ cổng thông tin chính thức Garena.

### Mục Lục
- [Kiến Trúc Hệ Thống (Layered Architecture)](#kiến-trúc-hệ-thống-layered-architecture)
- [Tính Năng Nổi Bật](#tính-năng-nổi-bật)
- [Cài Đặt](#cài-đặt-1)
- [Hướng Dẫn Sử Dụng](#hướng-dẫn-sử-dụng-1)
  - [1. Chạy Giao Diện Đồ Họa Desktop (GUI)](#1-chạy-giao-diện-đồ-họa-desktop-gui)
  - [2. Chạy Giao Diện Dòng Lệnh (CLI)](#2-chạy-giao-diện-dòng-lệnh-cli)
  - [3. Tích Hợp Thư Viện Python (SDK API)](#3-tích-hợp-thư-viện-python-sdk-api)
- [Hướng Dẫn Làm Mới & Cập Nhật Thông Số Tướng](#hướng-dẫn-làm-mới--cập-nhật-thông-số-tướng)
- [Bản Quyền & Tuyên Bố Từ Chối Trách Nhiệm](#bản-quyền--tuyên-bố-từ-chối-trách-nhiệm)

---

### Kiến Trúc Hệ Thống (Layered Architecture)

`aov-scrapecore` được thiết kế theo mô hình kiến trúc phân tầng 3 lớp (Three-Tier Layered Architecture) chuẩn mực, phân tách rành mạch giữa Nghiệp vụ cốt lõi (Domain), Tầng dịch vụ (Services), Tiện ích hệ thống (Utilities) và Tầng hiển thị (Presentation):

```text
aov-scrapecore/
├── scrapecore/
│   ├── core/                  # Tầng Domain: Thực thể dữ liệu & hằng số toàn cục
│   │   ├── constants.py       # Base URLs, User-Agent headers, ánh xạ vai trò tướng
│   │   └── models.py          # Data classes: Champion, Skill, Skin, DownloadResult
│   │
│   ├── services/              # Tầng Nghiệp vụ (Application / Business Logic)
│   │   ├── scraper_service.py # Xử lý kết nối HTTP, bóc tách DOM và trích xuất kỹ năng
│   │   ├── download_service.py# Tải tài nguyên đa luồng, kiểm tra trùng lặp và ghi đĩa
│   │   └── export_service.py  # Xuất cơ sở dữ liệu kỹ năng ra định dạng chuẩn JSON
│   │
│   ├── utils/                 # Tầng Hạ tầng & Tiện ích (Infrastructure)
│   │   ├── file_utils.py      # Chuẩn hóa tên tệp, ghi tệp an toàn nguyên khối (atomic)
│   │   └── text_utils.py      # Chuẩn hóa văn bản tiếng Việt Unicode NFD, lọc dấu
│   │
│   └── ui/                    # Tầng Trình diễn (Presentation Layer)
│       ├── cli/               # Giao diện dòng lệnh tương tác Menu & tham số
│       │   └── app.py
│       └── gui/               # Giao diện đồ họa Desktop Dark Theme (CustomTkinter)
│           └── app.py
│
├── main.py                    # Điểm khởi chạy chính của ứng dụng (Router CLI / GUI)
├── cli.py                     # Proxy tương thích ngược cho CLI
├── gui.py                     # Proxy tương thích ngược cho GUI
├── scraper.py                 # Proxy tương thích ngược cho Python API
├── data/
│   └── all_heroes_skills.json # Cơ sở dữ liệu hoàn chỉnh 129 tướng & toàn bộ chiêu thức
├── requirements.txt           # Danh sách thư viện phụ thuộc
├── run_cli.bat                # Khởi động nhanh CLI trên Windows (1-Click)
├── run_gui.bat                # Khởi động nhanh GUI trên Windows (1-Click)
└── LICENSE                    # Giấy phép MIT
```

---

### Tính Năng Nổi Bật

- **Bao quát đầy đủ 129+ vị tướng**: Tự động nhận diện và cập nhật cả những vị tướng mới nhất (Tamyn, Charlotte, Flowborn, Dyadia, v.v.).
- **Bóc tách sâu nội dung bài viết chiêu thức**: Bóc tách chính xác từ thẻ `<article>`, trích xuất toàn bộ công thức sát thương, tỉ lệ tăng tiến, thời gian hồi chiêu và cơ chế kích hoạt.
- **Tải đa luồng siêu tốc (Multi-threading)**: Quản lý hàng đợi tải bằng `ThreadPoolExecutor` với cơ chế retry tự động khi mạng chập chờn và bỏ qua tệp đã tải trước đó.
- **Hỗ trợ 2 giao diện người dùng**:
  - **Giao diện đồ họa Desktop (GUI)**: Viết bằng CustomTkinter với bộ lọc vai trò, thanh tìm kiếm thông minh, chọn nhiều tướng và nhật ký log trực quan.
  - **Giao diện dòng lệnh (CLI)**: Menu tương tác tiếng Việt và hệ thống tham số dòng lệnh phục vụ tự động hóa.
- **Xuất dữ liệu có cấu trúc**: Cung cấp file JSON chuẩn hóa cho các hệ thống phân tích, website hay ứng dụng bên thứ ba.

---

### Cài Đặt

#### Yêu cầu môi trường
- Python 3.10 trở lên
- Git

#### Các bước cài đặt
```bash
git clone https://github.com/Thien21112005/aov-scrapecore.git
cd aov-scrapecore

# Tạo môi trường ảo (khuyên dùng)
python -m venv venv
# Trên Windows:
venv\Scripts\activate
# Trên Linux/macOS:
source venv/bin/activate

# Cài đặt thư viện phụ thuộc
pip install -r requirements.txt
```

---

### Hướng Dẫn Sử Dụng

#### 1. Chạy Giao Diện Đồ Họa Desktop (GUI)
```bash
python main.py --gui
# hoặc nhấp đúp vào run_gui.bat trên Windows
```

#### 2. Chạy Giao Diện Dòng Lệnh (CLI)

##### Menu tương tác
```bash
python main.py
# hoặc python cli.py
```

##### Sử dụng qua tham số lệnh
```bash
# Tải ảnh của một vị tướng cụ thể
python cli.py --hero "Florentino"
python cli.py --hero "Tamyn"

# Tải theo vai trò
python cli.py --role "Xạ thủ"
python cli.py --role "Đấu sĩ"

# Tải toàn bộ 129 tướng
python cli.py --all

# Chỉ định loại ảnh: avatar, splash, skills hoặc all (mặc định: avatar,splash)
python cli.py --hero "Valhein" --type all

# Xuất dữ liệu toàn bộ kỹ năng 129 tướng ra file JSON
python cli.py --export-skills data/all_heroes_skills.json

# Cập nhật nhanh chiêu thức 1 tướng từ Garena và đồng bộ sang web
python cli.py --update-skills "Tamyn"

# Đồng bộ file JSON kỹ năng sang web AOV MetaForge (data.js)
python cli.py --sync-metaforge

# Tùy chỉnh thư mục lưu và số luồng tải
python cli.py --all --output "D:/Assets/AOV" --threads 8

# Xem danh sách tất cả các tướng
python cli.py --list
```

#### 3. Tích Hợp Thư Viện Python (SDK API)

```python
from scrapecore.services.scraper_service import ScraperService
from scrapecore.services.download_service import DownloadService
from scrapecore.services.export_service import ExportService

scraper = ScraperService(timeout=20)
downloader = DownloadService(scraper)
exporter = ExportService(scraper)

# 1. Lấy danh sách tướng
heroes = scraper.get_heroes()
print(f"Tổng số tướng: {len(heroes)}")

# 2. Bóc tách bộ chiêu thức chi tiết của một tướng
hero_url = "https://lienquan.garena.vn/hoc-vien/tuong-skin/d/tamyn/"
detail = scraper.get_hero_detail(hero_url)
for skill in detail["skills"]:
    print(f"[{skill['type']}] {skill['name']}: {skill['description'][:60]}...")

# 3. Xuất cơ sở dữ liệu đồng loạt
exporter.export_all_heroes_skills("data/all_heroes_skills.json", max_workers=10)
```

---

### Hướng Dẫn Làm Mới & Cập Nhật Thông Số Tướng

Khi game có bản cập nhật chỉnh sửa sức mạnh (Buff/Nerf), làm lại chiêu thức (Rework) hoặc ra mắt tướng mới, bạn có thể cập nhật dữ liệu qua 4 cách linh hoạt:

#### Cách 1: Cập nhật nhanh 1 tướng cụ thể từ Garena (Khuyên dùng khi có Patch nhỏ)
Khi chỉ có vài tướng được chỉnh sửa (ví dụ: *Tamyn*, *Florentino*, *Valhein*):
```bash
python cli.py --update-skills "Tamyn"
# hoặc
python sync_metaforge.py --hero "Florentino"
```
*Tác dụng: Tự động bóc tách bài viết mới nhất từ Garena, ghi vào `data/all_heroes_skills.json` và tự động cập nhật thẳng vào file `aov-metaforge/js/core/data.js` của web.*

#### Cách 2: Làm mới toàn bộ 129 tướng khi sang Mùa giải mới (Big Update)
Khi bước sang mùa giải mới hoặc cập nhật toàn diện:
```bash
python sync_metaforge.py --all
```
*Tác dụng: Tải lại toàn bộ 129 tướng đa luồng từ Garena và đồng bộ tức thì sang Web.*

#### Cách 3: Tự tay sửa thông số / Sát thương / Cơ chế theo ý muốn
Nếu trang Garena chưa kịp cập nhật hoặc bạn muốn tùy biến thông số thử nghiệm:
1. Mở file `data/all_heroes_skills.json`.
2. Tìm tên vị tướng (nhấn `Ctrl + F` tìm `"Tamyn"`).
3. Sửa trực tiếp chỉ số sát thương, hồi chiêu, mô tả trong trường `"description"`.
4. Đẩy toàn bộ thay đổi vừa sửa vào web bằng lệnh:
```bash
python cli.py --sync-metaforge
```

#### Cách 4: Tự đổi các thông số Meta (Tier S+, Độ cơ động, Điểm khống chế, Kèo khắc chế)
Các chỉ số chiến thuật phục vụ phân tích web nằm trong `aov-metaforge/js/core/data.js`:
- `"tier"`: `"S+"`, `"S"`, `"A"`, `"B"` (Cấp bậc sức mạnh meta)
- `"mobility"`: Điểm cơ động (1 - 100)
- `"cc_rating"`: Điểm khống chế cứng (1 - 100)
- `"countered_by"` / `"counters"`: Danh sách ID tướng khắc chế và bị khắc chế.
Chỉ cần sửa giá trị trong `data.js` và lưu lại, trang web sẽ nhận thông số mới ngay lập tức.

---

### Bản Quyền & Tuyên Bố Từ Chối Trách Nhiệm

Phát hành theo [Giấy phép MIT](LICENSE).

Toàn bộ hình ảnh, tài nguyên trang phục và nội dung trò chơi thuộc quyền sở hữu trí tuệ của **Tencent Games** và **Garena**. Repository này được xây dựng hoàn toàn vì mục đích học thuật, nghiên cứu kỹ thuật và phát triển công cụ tiện ích cho cộng đồng.

<p align="right"><a href="#aov-scrapecore">Lên đầu trang</a> &bull; <a href="#english">Switch to English</a></p>
