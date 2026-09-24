import random
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageOps, ImageTk

APP_TITLE = "图片随机测试"
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp"}
MIN_WINDOW_WIDTH = 760
MIN_WINDOW_HEIGHT = 600


@dataclass(frozen=True)
class ImageItem:
    path: Path
    answer: str


def discover_images(folder: Path) -> list[ImageItem]:
    """Read supported image files directly under folder, without recursion."""
    if not folder.is_dir():
        return []
    items: list[ImageItem] = []
    for path in folder.iterdir():
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            items.append(ImageItem(path=path, answer=path.stem))
    return sorted(items, key=lambda item: item.path.name.casefold())


def choose_test_items(all_items: list[ImageItem], count: int) -> list[ImageItem]:
    """Randomly choose count distinct items and shuffle their order."""
    if count < 1:
        raise ValueError("测试数量必须至少为 1。")
    if count > len(all_items):
        raise ValueError("测试数量不能超过图片总数。")
    return random.sample(all_items, count)


def load_display_image(path: Path, max_width: int, max_height: int) -> Image.Image:
    """Open one image safely and resize it to fit the display area, preserving aspect ratio."""
    with Image.open(path) as source:
        image = ImageOps.exif_transpose(source)
        try:
            image.seek(0)  # GIF/WebP may be animated; use the first frame for predictability.
        except EOFError:
            pass
        image = image.convert("RGBA")
        if max_width <= 0 or max_height <= 0:
            return image.copy()
        fitted = ImageOps.contain(image, (max_width, max_height), method=Image.Resampling.LANCZOS)
        return fitted.copy()


class ImageQuizApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1000x760")
        self.minsize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)

        self.all_items: list[ImageItem] = []
        self.selected_items: list[ImageItem] = []
        self.current_index = 0
        self.answer_revealed = False
        self.current_photo: Optional[ImageTk.PhotoImage] = None
        self.current_image_error: Optional[str] = None
        self._resize_job: Optional[str] = None

        self.folder_var = tk.StringVar()
        self.count_var = tk.StringVar(value="10")
        self.info_var = tk.StringVar(value="请选择图片文件夹。")
        self.answer_var = tk.StringVar(value="")
        self.progress_var = tk.StringVar(value="")
        self.hint_var = tk.StringVar(value="看图片，想好答案后按“确定”。")

        self.style = ttk.Style(self)
        try:
            self.style.theme_use("vista")
        except tk.TclError:
            pass
        self._configure_styles()

        self.container = ttk.Frame(self, padding=18)
        self.container.pack(fill="both", expand=True)
        self.container.rowconfigure(0, weight=1)
        self.container.columnconfigure(0, weight=1)

        self._build_settings_page()
        self._build_quiz_page()
        self._build_finished_page()
        self.show_settings()

        self.bind("<Return>", self._on_enter)
        self.bind("<Escape>", self._on_escape)

    def _configure_styles(self) -> None:
        self.style.configure("Title.TLabel", font=("Microsoft YaHei UI", 22, "bold"))
        self.style.configure("Section.TLabel", font=("Microsoft YaHei UI", 12, "bold"))
        self.style.configure("BigButton.TButton", font=("Microsoft YaHei UI", 13, "bold"), padding=(22, 12))
        self.style.configure("Answer.TLabel", font=("Microsoft YaHei UI", 22, "bold"), anchor="center")
        self.style.configure("Progress.TLabel", font=("Microsoft YaHei UI", 11))
        self.style.configure("Hint.TLabel", font=("Microsoft YaHei UI", 10))
        self.style.configure("Count.TSpinbox", font=("Microsoft YaHei UI", 12))

    def _build_settings_page(self) -> None:
        self.settings_frame = ttk.Frame(self.container)
        self.settings_frame.columnconfigure(0, weight=1)

        ttk.Label(self.settings_frame, text=APP_TITLE, style="Title.TLabel").grid(
            row=0, column=0, pady=(40, 10)
        )
        ttk.Label(
            self.settings_frame,
            text="选择一个图片文件夹，然后设置本轮测试数量。",
            font=("Microsoft YaHei UI", 11),
        ).grid(row=1, column=0, pady=(0, 32))

        card = ttk.Frame(self.settings_frame, padding=28, relief="groove", borderwidth=1)
        card.grid(row=2, column=0, sticky="ew", padx=90)
        card.columnconfigure(1, weight=1)

        ttk.Label(card, text="图片文件夹", style="Section.TLabel").grid(
            row=0, column=0, sticky="w", padx=(0, 12), pady=10
        )
        self.folder_entry = ttk.Entry(card, textvariable=self.folder_var, state="readonly")
        self.folder_entry.grid(row=0, column=1, sticky="ew", pady=10)
        ttk.Button(card, text="选择文件夹", command=self.select_folder).grid(
            row=0, column=2, padx=(12, 0), pady=10
        )

        ttk.Label(card, text="本轮测试数量", style="Section.TLabel").grid(
            row=1, column=0, sticky="w", padx=(0, 12), pady=10
        )
        self.count_spinbox = ttk.Spinbox(
            card, from_=1, to=999999, textvariable=self.count_var, width=10, style="Count.TSpinbox"
        )
        self.count_spinbox.grid(row=1, column=1, sticky="w", pady=10)
        ttk.Label(card, text="张", font=("Microsoft YaHei UI", 11)).grid(
            row=1, column=2, sticky="w", padx=(8, 0), pady=10
        )

        ttk.Label(self.settings_frame, textvariable=self.info_var, font=("Microsoft YaHei UI", 11)).grid(
            row=3, column=0, pady=(18, 8)
        )
        ttk.Button(self.settings_frame, text="开始测试", style="BigButton.TButton", command=self.start_test).grid(
            row=4, column=0, pady=(12, 10)
        )
        ttk.Label(
            self.settings_frame,
            text="快捷键：Enter 开始/确认/下一步　 Esc 返回设置或退出测试",
            style="Hint.TLabel",
        ).grid(row=5, column=0, pady=(14, 0))

    def _build_quiz_page(self) -> None:
        self.quiz_frame = ttk.Frame(self.container)
        self.quiz_frame.rowconfigure(1, weight=1)
        self.quiz_frame.columnconfigure(0, weight=1)

        top = ttk.Frame(self.quiz_frame)
        top.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        top.columnconfigure(0, weight=1)
        ttk.Label(top, textvariable=self.progress_var, style="Progress.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Button(top, text="返回设置", command=self.show_settings).grid(row=0, column=1, padx=(10, 0))

        self.image_area = ttk.Frame(self.quiz_frame, relief="solid", borderwidth=1)
        self.image_area.grid(row=1, column=0, sticky="nsew")
        self.image_area.rowconfigure(0, weight=1)
        self.image_area.columnconfigure(0, weight=1)
        self.image_label = ttk.Label(self.image_area, anchor="center", justify="center")
        self.image_label.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)
        self.image_area.bind("<Configure>", self._schedule_image_refresh)

        bottom = ttk.Frame(self.quiz_frame, padding=(0, 12, 0, 0))
        bottom.grid(row=2, column=0, sticky="ew")
        bottom.columnconfigure(0, weight=1)
        bottom.columnconfigure(1, weight=1)
        bottom.columnconfigure(2, weight=1)

        self.answer_label = ttk.Label(bottom, textvariable=self.answer_var, style="Answer.TLabel")
        self.answer_label.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 10))
        self.hint_label = ttk.Label(bottom, textvariable=self.hint_var, style="Hint.TLabel", anchor="center")
        self.hint_label.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(0, 10))

        self.prev_button = ttk.Button(bottom, text="上一张", command=self.previous_image)
        self.prev_button.grid(row=2, column=0, sticky="e", padx=5)
        self.confirm_button = ttk.Button(bottom, text="确定", style="BigButton.TButton", command=self.confirm_step)
        self.confirm_button.grid(row=2, column=1, sticky="n", padx=5)
        ttk.Label(bottom, text="", width=12).grid(row=2, column=2, sticky="w")

    def _build_finished_page(self) -> None:
        self.finished_frame = ttk.Frame(self.container)
        self.finished_frame.columnconfigure(0, weight=1)
        ttk.Label(self.finished_frame, text="本轮测试完成！", style="Title.TLabel").grid(
            row=0, column=0, pady=(100, 18)
        )
        ttk.Label(
            self.finished_frame, textvariable=self.progress_var, font=("Microsoft YaHei UI", 14)
        ).grid(row=1, column=0, pady=(0, 28))
        ttk.Button(
            self.finished_frame, text="重新开始", style="BigButton.TButton", command=self.restart_test
        ).grid(row=2, column=0, pady=8)
        ttk.Button(
            self.finished_frame, text="返回设置", style="BigButton.TButton", command=self.show_settings
        ).grid(row=3, column=0, pady=8)

    def _hide_all_pages(self) -> None:
        for frame in (self.settings_frame, self.quiz_frame, self.finished_frame):
            frame.grid_remove()

    def show_settings(self) -> None:
        self._hide_all_pages()
        self.settings_frame.grid(row=0, column=0, sticky="nsew")
        if self.folder_var.get():
            folder = Path(self.folder_var.get())
            self.all_items = discover_images(folder)
            self._update_folder_info()
        self.after_idle(lambda: self.count_spinbox.focus_set())

    def _update_folder_info(self) -> None:
        if not self.folder_var.get():
            self.info_var.set("请选择图片文件夹。")
            return
        count = len(self.all_items)
        if count:
            self.info_var.set(f"当前文件夹找到 {count} 张支持的图片。")
        else:
            self.info_var.set("当前文件夹中没有找到支持的图片文件。")

    def select_folder(self) -> None:
        initial = self.folder_var.get() if self.folder_var.get() else str(Path.home())
        folder = filedialog.askdirectory(title="选择图片文件夹", initialdir=initial)
        if not folder:
            return
        self.folder_var.set(folder)
        self.all_items = discover_images(Path(folder))
        self._update_folder_info()
        if self.all_items:
            current = self.count_var.get().strip()
            try:
                count = int(current)
            except ValueError:
                count = 10
            self.count_var.set(str(min(max(count, 1), len(self.all_items))))

    def _read_test_count(self) -> Optional[int]:
        raw = self.count_var.get().strip()
        try:
            count = int(raw)
        except ValueError:
            messagebox.showwarning("数量无效", "请输入一个正整数作为本轮测试数量。", parent=self)
            return None
        if count < 1:
            messagebox.showwarning("数量无效", "本轮测试数量必须至少为 1。", parent=self)
            return None
        if count > len(self.all_items):
            messagebox.showwarning(
                "数量超过图片总数",
                f"当前文件夹中共有 {len(self.all_items)} 张图片，\n测试数量不能设置为 {count} 张。",
                parent=self,
            )
            return None
        return count

    def start_test(self) -> None:
        folder_text = self.folder_var.get().strip()
        if not folder_text:
            messagebox.showwarning("尚未选择文件夹", "请先选择一个图片文件夹。", parent=self)
            return
        folder = Path(folder_text)
        self.all_items = discover_images(folder)
        if not self.all_items:
            messagebox.showwarning("没有图片", "当前文件夹中没有找到支持的图片文件。", parent=self)
            return
        count = self._read_test_count()
        if count is None:
            return
        self.selected_items = choose_test_items(self.all_items, count)
        self.current_index = 0
        self.answer_revealed = False
        self.current_photo = None
        self.current_image_error = None
        self._show_quiz()

    def restart_test(self) -> None:
        if not self.all_items:
            self.show_settings()
            return
        self.start_test()

    def _show_quiz(self) -> None:
        self._hide_all_pages()
        self.quiz_frame.grid(row=0, column=0, sticky="nsew")
        self._display_current_image()
        self.after_idle(lambda: self.confirm_button.focus_set())

    def _display_current_image(self) -> None:
        if not self.selected_items:
            return
        self.answer_revealed = False
        self.answer_var.set("")
        self.hint_var.set("看图片，想好答案后按“确定”。")
        self.confirm_button.configure(text="确定")
        self.prev_button.configure(state="normal" if self.current_index > 0 else "disabled")
        self.progress_var.set(f"第 {self.current_index + 1} / {len(self.selected_items)} 张")
        self.current_photo = None
        self.current_image_error = None
        self.image_label.configure(text="正在加载图片…", image="")
        self._refresh_image()

    def _schedule_image_refresh(self, _event=None) -> None:
        if self._resize_job is not None:
            try:
                self.after_cancel(self._resize_job)
            except tk.TclError:
                pass
        self._resize_job = self.after(60, self._refresh_image)

    def _refresh_image(self) -> None:
        self._resize_job = None
        if not self.selected_items:
            return
        item = self.selected_items[self.current_index]
        width = max(1, self.image_area.winfo_width() - 24)
        height = max(1, self.image_area.winfo_height() - 24)
        try:
            image = load_display_image(item.path, width, height)
            self.current_photo = ImageTk.PhotoImage(image=image)
            self.image_label.configure(image=self.current_photo, text="")
            self.current_image_error = None
        except Exception as exc:  # A bad image must not crash the whole quiz.
            self.current_photo = None
            self.current_image_error = str(exc)
            self.hint_var.set("这张图片无法读取，按“确定”跳过此图片。")
            self.image_label.configure(
                image="",
                text="这张图片无法读取。\n按“确定”跳过此图片。",
                font=("Microsoft YaHei UI", 14),
                anchor="center",
            )

    def confirm_step(self) -> None:
        if not self.selected_items:
            return
        if self.current_image_error:
            self._go_next()
            return
        if not self.answer_revealed:
            self.answer_revealed = True
            answer = self.selected_items[self.current_index].answer
            self.answer_var.set(f"答案：{answer}")
            self.hint_var.set("再按一次“确定”进入下一张。")
            return
        self._go_next()

    def _go_next(self) -> None:
        if self.current_index >= len(self.selected_items) - 1:
            total = len(self.selected_items)
            self.progress_var.set(f"共测试：{total} 张")
            self._show_finished()
            return
        self.current_index += 1
        self._display_current_image()

    def previous_image(self) -> None:
        if not self.selected_items or self.current_index <= 0:
            return
        self.current_index -= 1
        self._display_current_image()

    def _show_finished(self) -> None:
        self._hide_all_pages()
        self.finished_frame.grid(row=0, column=0, sticky="nsew")
        self.after_idle(lambda: self.finished_frame.focus_set())

    def _on_enter(self, _event=None) -> str:
        current = self.focus_get()
        if current == self.count_spinbox:
            self.start_test()
            return "break"
        if self.quiz_frame.winfo_ismapped():
            self.confirm_step()
            return "break"
        if self.finished_frame.winfo_ismapped():
            self.restart_test()
            return "break"
        return "break"

    def _on_escape(self, _event=None) -> str:
        if self.quiz_frame.winfo_ismapped() or self.finished_frame.winfo_ismapped():
            self.show_settings()
            return "break"
        return "break"


def main() -> None:
    app = ImageQuizApp()
    app.mainloop()


if __name__ == "__main__":
    main()
