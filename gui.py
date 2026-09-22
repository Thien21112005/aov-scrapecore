"""
Modern Graphical User Interface (GUI) for Lien Quan Mobile Image Downloader
Using CustomTkinter for a sleek, responsive dark-themed UI.
"""

import os
import sys
import threading
import queue
import subprocess
from tkinter import filedialog, messagebox
import customtkinter as ctk

from scraper import AOVScraper, strip_accents, sanitize_filename

# Set appearance and theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class AOVDownloaderGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Liên Quân Mobile - Tool Tải Ảnh Tướng & Trang Phục Full HD")
        self.geometry("980x720")
        self.minsize(850, 600)

        self.scraper = AOVScraper()
        self.all_heroes = []
        self.hero_checkboxes = {}  # hero_id -> (CTkCheckBox, hero_data)
        self.log_queue = queue.Queue()
        self.is_downloading = False
        self.stop_requested = False

        self._build_ui()
        self.after(100, self._load_heroes_initial)
        self.after(100, self._process_log_queue)

    def _build_ui(self):
        # Configure grid 2 columns: Left (Selection, 380px), Right (Config & Log, remaining)
        self.grid_columnconfigure(0, weight=4)
        self.grid_columnconfigure(1, weight=6)
        self.grid_rowconfigure(0, weight=1)

        # ==========================================
        # LEFT FRAME: Heroes selection & search
        # ==========================================
        left_frame = ctk.CTkFrame(self, corner_radius=12)
        left_frame.grid(row=0, column=0, padx=(15, 8), pady=15, sticky="nsew")
        left_frame.grid_rowconfigure(3, weight=1)
        left_frame.grid_columnconfigure(0, weight=1)

        # Title
        title_label = ctk.CTkLabel(
            left_frame,
            text="⚔️ Danh Sách Vị Tướng",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.grid(row=0, column=0, padx=12, pady=(12, 6), sticky="w")

        # Filter bar: Search + Role dropdown
        filter_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        filter_frame.grid(row=1, column=0, padx=12, pady=4, sticky="ew")
        filter_frame.grid_columnconfigure(0, weight=1)

        self.search_entry = ctk.CTkEntry(
            filter_frame,
            placeholder_text="🔍 Tìm tướng (vd: Flo, Val, Qi...)"
        )
        self.search_entry.grid(row=0, column=0, padx=(0, 6), pady=2, sticky="ew")
        self.search_entry.bind("<KeyRelease>", lambda e: self._filter_heroes())

        self.role_combobox = ctk.CTkComboBox(
            filter_frame,
            values=["Tất cả vai trò", "Đấu sĩ", "Đỡ đòn", "Pháp sư", "Sát thủ", "Trợ thủ", "Xạ thủ"],
            command=lambda val: self._filter_heroes(),
            width=120
        )
        self.role_combobox.set("Tất cả vai trò")
        self.role_combobox.grid(row=0, column=1, padx=0, pady=2)

        # Quick select buttons
        btn_select_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        btn_select_frame.grid(row=2, column=0, padx=12, pady=(6, 4), sticky="ew")
        btn_select_frame.grid_columnconfigure(0, weight=1)
        btn_select_frame.grid_columnconfigure(1, weight=1)

        self.btn_select_all = ctk.CTkButton(
            btn_select_frame,
            text="Chọn tất cả",
            command=self._select_all_visible,
            height=28,
            fg_color="#2b5c8f",
            hover_color="#1f4266"
        )
        self.btn_select_all.grid(row=0, column=0, padx=(0, 4), sticky="ew")

        self.btn_deselect_all = ctk.CTkButton(
            btn_select_frame,
            text="Bỏ chọn",
            command=self._deselect_all,
            height=28,
            fg_color="#444444",
            hover_color="#333333"
        )
        self.btn_deselect_all.grid(row=0, column=1, padx=(4, 0), sticky="ew")

        # Scrollable Heroes List
        self.heroes_scroll = ctk.CTkScrollableFrame(left_frame, label_text="Đang tải danh sách...")
        self.heroes_scroll.grid(row=3, column=0, padx=12, pady=(4, 12), sticky="nsew")

        # Selected counter label
        self.counter_label = ctk.CTkLabel(
            left_frame,
            text="Đã chọn: 0 tướng",
            font=ctk.CTkFont(size=12),
            text_color="#999999"
        )
        self.counter_label.grid(row=4, column=0, padx=12, pady=(0, 10), sticky="w")

        # ==========================================
        # RIGHT FRAME: Settings, Progress & Logs
        # ==========================================
        right_frame = ctk.CTkFrame(self, corner_radius=12)
        right_frame.grid(row=0, column=1, padx=(8, 15), pady=15, sticky="nsew")
        right_frame.grid_rowconfigure(4, weight=1)
        right_frame.grid_columnconfigure(0, weight=1)

        # Settings header
        settings_title = ctk.CTkLabel(
            right_frame,
            text="⚙️ Thiết Lập Tải Xuống",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        settings_title.grid(row=0, column=0, padx=15, pady=(12, 8), sticky="w")

        # Output folder config
        folder_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        folder_frame.grid(row=1, column=0, padx=15, pady=4, sticky="ew")
        folder_frame.grid_columnconfigure(1, weight=1)

        folder_lbl = ctk.CTkLabel(folder_frame, text="Thư mục lưu:", width=90, anchor="w")
        folder_lbl.grid(row=0, column=0, padx=(0, 8), pady=2)

        default_dir = os.path.abspath(os.path.join(os.getcwd(), "downloads"))
        self.dir_entry = ctk.CTkEntry(folder_frame)
        self.dir_entry.insert(0, default_dir)
        self.dir_entry.grid(row=0, column=1, padx=(0, 8), pady=2, sticky="ew")

        btn_browse = ctk.CTkButton(
            folder_frame,
            text="Chọn...",
            width=70,
            command=self._browse_folder
        )
        btn_browse.grid(row=0, column=2, pady=2)

        # Image Types & Threads options
        options_frame = ctk.CTkFrame(right_frame, corner_radius=8)
        options_frame.grid(row=2, column=0, padx=15, pady=8, sticky="ew")
        options_frame.grid_columnconfigure(0, weight=1)
        options_frame.grid_columnconfigure(1, weight=1)
        options_frame.grid_columnconfigure(2, weight=1)

        self.cb_avatar = ctk.CTkCheckBox(options_frame, text="Ảnh đại diện (Avatar)")
        self.cb_avatar.select()
        self.cb_avatar.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.cb_splash = ctk.CTkCheckBox(options_frame, text="Trang phục HD (1080p)")
        self.cb_splash.select()
        self.cb_splash.grid(row=0, column=1, padx=10, pady=10, sticky="w")

        self.cb_skills = ctk.CTkCheckBox(options_frame, text="Chiêu thức (Skills)")
        self.cb_skills.grid(row=0, column=2, padx=10, pady=10, sticky="w")

        # Slider threads
        thread_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        thread_frame.grid(row=3, column=0, padx=15, pady=4, sticky="ew")
        thread_frame.grid_columnconfigure(1, weight=1)

        self.lbl_threads = ctk.CTkLabel(thread_frame, text="Số luồng tải: 6")
        self.lbl_threads.grid(row=0, column=0, padx=(0, 10), sticky="w")

        self.slider_threads = ctk.CTkSlider(
            thread_frame,
            from_=1,
            to=16,
            number_of_steps=15,
            command=self._on_slider_change
        )
        self.slider_threads.set(6)
        self.slider_threads.grid(row=0, column=1, sticky="ew")

        # Action Buttons & Progress
        action_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        action_frame.grid(row=4, column=0, padx=15, pady=6, sticky="ew")
        action_frame.grid_columnconfigure(0, weight=2)
        action_frame.grid_columnconfigure(1, weight=1)
        action_frame.grid_columnconfigure(2, weight=1)

        self.btn_download = ctk.CTkButton(
            action_frame,
            text="🚀 BẮT ĐẦU TẢI VỀ",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#28a745",
            hover_color="#218838",
            height=36,
            command=self._start_download
        )
        self.btn_download.grid(row=0, column=0, padx=(0, 8), sticky="ew")

        self.btn_stop = ctk.CTkButton(
            action_frame,
            text="⛔ Dừng",
            font=ctk.CTkFont(size=13),
            fg_color="#dc3545",
            hover_color="#c82333",
            height=36,
            state="disabled",
            command=self._stop_download
        )
        self.btn_stop.grid(row=0, column=1, padx=(0, 8), sticky="ew")

        self.btn_open_folder = ctk.CTkButton(
            action_frame,
            text="📂 Mở thư mục",
            font=ctk.CTkFont(size=13),
            height=36,
            fg_color="#17a2b8",
            hover_color="#138496",
            command=self._open_output_dir
        )
        self.btn_open_folder.grid(row=0, column=2, sticky="ew")

        # Progress bar + status
        progress_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        progress_frame.grid(row=5, column=0, padx=15, pady=(4, 6), sticky="ew")
        progress_frame.grid_columnconfigure(0, weight=1)

        self.lbl_status = ctk.CTkLabel(
            progress_frame,
            text="Sẵn sàng...",
            font=ctk.CTkFont(size=12),
            anchor="w"
        )
        self.lbl_status.grid(row=0, column=0, sticky="w", pady=(0, 2))

        self.progress_bar = ctk.CTkProgressBar(progress_frame)
        self.progress_bar.set(0.0)
        self.progress_bar.grid(row=1, column=0, sticky="ew")

        # Console Log
        self.log_text = ctk.CTkTextbox(
            right_frame,
            font=ctk.CTkFont(family="Consolas", size=11),
            corner_radius=8
        )
        self.log_text.grid(row=6, column=0, padx=15, pady=(4, 15), sticky="nsew")
        right_frame.grid_rowconfigure(6, weight=1)

    def _on_slider_change(self, val):
        self.lbl_threads.configure(text=f"Số luồng tải: {int(val)}")

    def _browse_folder(self):
        dir_selected = filedialog.askdirectory(initialdir=self.dir_entry.get())
        if dir_selected:
            self.dir_entry.delete(0, "end")
            self.dir_entry.insert(0, dir_selected)

    def _open_output_dir(self):
        target = self.dir_entry.get().strip()
        if not os.path.exists(target):
            os.makedirs(target, exist_ok=True)
        if sys.platform == "win32":
            os.startfile(target)
        else:
            subprocess.Popen(["xdg-open", target])

    def _log(self, message: str):
        self.log_queue.put(message)

    def _process_log_queue(self):
        while not self.log_queue.empty():
            msg = self.log_queue.get_nowait()
            self.log_text.insert("end", msg + "\n")
            self.log_text.see("end")
        self.after(80, self._process_log_queue)

    def _load_heroes_initial(self):
        self._log("[*] Đang kết nối tới website Liên Quân Mobile...")
        def fetch_task():
            try:
                heroes = self.scraper.get_heroes()
                self.all_heroes = heroes
                self.after(0, self._render_heroes_list)
            except Exception as e:
                self._log(f"[!] Lỗi tải danh sách: {e}")
                self.after(0, lambda: self.lbl_status.configure(text=f"Lỗi: {e}"))

        threading.Thread(target=fetch_task, daemon=True).start()

    def _render_heroes_list(self):
        self.heroes_scroll.configure(label_text=f"Danh sách ({len(self.all_heroes)} tướng)")
        self._log(f"[✓] Đã tải danh sách {len(self.all_heroes)} vị tướng.")
        self.lbl_status.configure(text=f"Đã nạp {len(self.all_heroes)} tướng.")

        # Clear existing
        for widget in self.heroes_scroll.winfo_children():
            widget.destroy()
        self.hero_checkboxes.clear()

        # Render checkboxes
        for idx, hero in enumerate(self.all_heroes):
            roles_str = ", ".join(hero["roles"])
            text = f"{hero['name']} ({roles_str})"
            cb = ctk.CTkCheckBox(
                self.heroes_scroll,
                text=text,
                command=self._update_counter
            )
            cb.grid(row=idx, column=0, padx=8, pady=3, sticky="w")
            self.hero_checkboxes[hero["id"]] = (cb, hero)

        self._update_counter()

    def _filter_heroes(self):
        search_kw = strip_accents(self.search_entry.get().strip())
        role_filter = self.role_combobox.get()

        for hero_id, (cb, hero) in self.hero_checkboxes.items():
            name_match = (
                search_kw in strip_accents(hero["name"])
                or search_kw in strip_accents(hero["id"])
            )
            role_match = (
                role_filter == "Tất cả vai trò"
                or role_filter in hero["roles"]
            )

            if name_match and role_match:
                cb.grid()
            else:
                cb.grid_remove()

    def _select_all_visible(self):
        for cb, hero in self.hero_checkboxes.values():
            if cb.winfo_ismapped():
                cb.select()
        self._update_counter()

    def _deselect_all(self):
        for cb, hero in self.hero_checkboxes.values():
            cb.deselect()
        self._update_counter()

    def _update_counter(self):
        selected = sum(1 for cb, _ in self.hero_checkboxes.values() if cb.get() == 1)
        self.counter_label.configure(text=f"Đã chọn: {selected} / {len(self.all_heroes)} tướng")

    def _get_selected_heroes(self) -> list[dict]:
        return [hero for cb, hero in self.hero_checkboxes.values() if cb.get() == 1]

    def _start_download(self):
        selected_heroes = self._get_selected_heroes()
        if not selected_heroes:
            messagebox.showwarning("Thông báo", "Vui lòng chọn ít nhất một vị tướng để tải ảnh!")
            return

        img_types = []
        if self.cb_avatar.get():
            img_types.append("avatar")
        if self.cb_splash.get():
            img_types.append("splash")
        if self.cb_skills.get():
            img_types.append("skills")

        if not img_types:
            messagebox.showwarning("Thông báo", "Vui lòng chọn ít nhất một loại ảnh (Avatar / Trang phục / Chiêu thức)!")
            return

        out_dir = self.dir_entry.get().strip()
        if not out_dir:
            messagebox.showwarning("Thông báo", "Vui lòng chọn thư mục lưu ảnh!")
            return

        threads = int(self.slider_threads.get())

        self.is_downloading = True
        self.stop_requested = False
        self.btn_download.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self.progress_bar.set(0.0)

        self._log("\n" + "=" * 45)
        self._log(f"[*] Bắt đầu tải {len(selected_heroes)} tướng...")
        self._log(f"[*] Thư mục lưu: {out_dir}")
        self._log(f"[*] Loại ảnh: {', '.join(img_types)} | Số luồng: {threads}")
        self._log("=" * 45)

        def worker():
            total = len(selected_heroes)
            finished_heroes = 0
            stats = {"avatar": 0, "skins": 0, "skills": 0, "failed": 0}

            def callback(hero_name, item_name, ok, is_finished=False):
                nonlocal finished_heroes
                if self.stop_requested:
                    return

                if is_finished:
                    finished_heroes += 1
                    pct = finished_heroes / total
                    self.after(0, lambda p=pct: self.progress_bar.set(p))
                    self.after(
                        0,
                        lambda fn=finished_heroes, h=hero_name: self.lbl_status.configure(
                            text=f"Tiến độ: {fn}/{total} tướng (Vừa xong: {h})"
                        )
                    )
                else:
                    status_str = "✓" if ok else "✗"
                    self._log(f"  [{status_str}] {hero_name} -> {item_name}")

            results = self.scraper.download_heroes_batch(
                heroes=selected_heroes,
                output_dir=out_dir,
                image_types=img_types,
                max_workers=threads,
                callback=callback,
                cancel_check=lambda: self.stop_requested
            )

            for r in results:
                stats["avatar"] += r.get("avatar", 0)
                stats["skins"] += r.get("skins", 0)
                stats["skills"] += r.get("skills", 0)
                stats["failed"] += r.get("failed", 0)

            self.after(0, lambda: self._on_download_finished(stats, total))

        threading.Thread(target=worker, daemon=True).start()

    def _stop_download(self):
        if self.is_downloading:
            self.stop_requested = True
            self._log("[!] Đã gửi yêu cầu dừng tải...")
            self.btn_stop.configure(state="disabled")

    def _on_download_finished(self, stats: dict, total: int):
        self.is_downloading = False
        self.btn_download.configure(state="normal")
        self.btn_stop.configure(state="disabled")

        if self.stop_requested:
            self.lbl_status.configure(text="Đã dừng tải theo yêu cầu.")
            self._log("[!] Quá trình tải đã dừng lại.")
        else:
            self.progress_bar.set(1.0)
            self.lbl_status.configure(text=f"Hoàn tất tải về {total} tướng!")
            self._log("\n" + "=" * 45)
            self._log(f"[✓] HOÀN TẤT TẢI VỀ!")
            self._log(f"  - Tổng Avatar:        {stats['avatar']}")
            self._log(f"  - Tổng Trang phục HD: {stats['skins']}")
            self._log(f"  - Tổng Kỹ năng:       {stats['skills']}")
            if stats["failed"] > 0:
                self._log(f"  - Tải lỗi:            {stats['failed']}")
            self._log(f"  - Thư mục lưu: {self.dir_entry.get().strip()}")
            self._log("=" * 45)

            messagebox.showinfo(
                "Thành công",
                f"Đã hoàn tất tải ảnh cho các tướng đã chọn!\n\n"
                f"• Avatar: {stats['avatar']}\n"
                f"• Trang phục HD: {stats['skins']}\n"
                f"• Kỹ năng: {stats['skills']}\n\n"
                f"Được lưu tại:\n{self.dir_entry.get().strip()}"
            )


def launch_gui():
    app = AOVDownloaderGUI()
    app.mainloop()


if __name__ == "__main__":
    launch_gui()
