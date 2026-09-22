"""Core constants and definitions."""

BASE_URL = "https://lienquan.garena.vn/hoc-vien/tuong-skin/"

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "vi,en-US;q=0.9,en;q=0.8",
}

ROLE_MAP = {
    28: "Đấu sĩ",
    31: "Đỡ đòn",
    29: "Pháp sư",
    32: "Sát thủ",
    30: "Trợ thủ",
    33: "Xạ thủ",
}

SKILL_TYPE_LABELS = [
    "Nội tại",
    "Chiêu 1",
    "Chiêu 2",
    "Chiêu 3 (Chiêu cuối)",
    "Chiêu 4",
    "Chiêu 5"
]
