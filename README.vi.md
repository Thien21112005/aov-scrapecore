# AOV ScrapeCore

> Công cụ cào và trích xuất tài nguyên, kỹ năng tướng Liên Quân Mobile (Arena of Valor) hiệu năng cao.

[English](README.md) | [Tiếng Việt](README.vi.md)

[![Phiên bản Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Giấy phép: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Kiến trúc: Layered](https://img.shields.io/badge/architecture-layered%20clean-emerald.svg)](https://en.wikipedia.org/wiki/Multitier_architecture)

Engine cào dữ liệu và tải xuống tài nguyên được thiết kế chuyên sâu để trích xuất siêu dữ liệu, hình nền trang phục Full HD (1920x1080), ảnh đại diện avatar, bộ chiêu thức và nội dung mô tả chỉ số cơ chế của toàn bộ các vị tướng Liên Quân Mobile từ cổng thông tin chính thức Garena.

---

## Kiến Trúc Hệ Thống (Layered Architecture)

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

## Tính Năng Nổi Bật

- **Bao quát đầy đủ 129+ vị tướng**: Tự động nhận diện và cập nhật cả những vị tướng mới nhất (Tamyn, Charlotte, Flowborn, Dyadia, v.v.).
- **Bóc tách sâu nội dung bài viết chiêu thức**: Bóc tách chính xác từ thẻ `<article>`, trích xuất toàn bộ công thức sát thương, tỉ lệ tăng tiến, thời gian hồi chiêu và cơ chế kích hoạt.
- **Tải đa luồng siêu tốc (Multi-threading)**: Quản lý hàng đợi tải bằng `ThreadPoolExecutor` với cơ chế retry tự động khi mạng chập chờn và bỏ qua tệp đã tải trước đó.
- **Hỗ trợ 2 giao diện người dùng**:
  - **Giao diện đồ họa Desktop (GUI)**: Viết bằng CustomTkinter với bộ lọc vai trò, thanh tìm kiếm thông minh, chọn nhiều tướng và nhật ký log trực quan.
  - **Giao diện dòng lệnh (CLI)**: Menu tương tác tiếng Việt và hệ thống tham số dòng lệnh phục vụ tự động hóa.
- **Xuất dữ liệu có cấu trúc**: Cung cấp file JSON chuẩn hóa cho các hệ thống phân tích, website hay ứng dụng bên thứ ba.

---

## Cài Đặt

### Yêu cầu môi trường
- Python 3.10 trở lên
- Git

### Các bước cài đặt
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

## Hướng Dẫn Sử Dụng

### 1. Chạy Giao Diện Đồ Họa Desktop (GUI)
```bash
python main.py --gui
# hoặc nhấp đúp vào run_gui.bat trên Windows
```

### 2. Chạy Giao Diện Dòng Lệnh (CLI)

#### Menu tương tác
```bash
python main.py
# hoặc python cli.py
```

#### Sử dụng qua tham số lệnh
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

# Tùy chỉnh thư mục lưu và số luồng tải
python cli.py --all --output "D:/Assets/AOV" --threads 8

# Xem danh sách tất cả các tướng
python cli.py --list
```

### 3. Tích Hợp Thư Viện Python (SDK API)

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

## Bản Quyền & Tuyên Bố Từ Chối Trách Nhiệm

Phát hành theo [Giấy phép MIT](LICENSE).

Toàn bộ hình ảnh, tài nguyên trang phục và nội dung trò chơi thuộc quyền sở hữu trí tuệ của **Tencent Games** và **Garena**. Repository này được xây dựng hoàn toàn vì mục đích học thuật, nghiên cứu kỹ thuật và phát triển công cụ tiện ích cho cộng đồng.
