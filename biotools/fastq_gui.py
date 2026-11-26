"""Графический интерфейс (урезанный FastQC) для модуля biotools.fastq."""
import os
import re
import sys
from tkinter import filedialog, messagebox, ttk
import tkinter as tk
from urllib.parse import unquote, urlparse

try:
    from .fastq import FastqReader
except ImportError:
    _ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _ROOT not in sys.path:
        sys.path.insert(0, _ROOT)
    from biotools.fastq import FastqReader

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_DND = True
except ImportError:
    DND_FILES = None
    TkinterDnD = None
    HAS_DND = False

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from matplotlib.gridspec import GridSpec

SUPPORTED_EXTENSIONS = (".fastq", ".fq", ".fastq.gz", ".fq.gz")
FASTQ_FILETYPES = [
    ("FASTQ файлы", "*.fastq *.fq *.fastq.gz *.fq.gz"),
    ("Несжатый FASTQ", "*.fastq *.fq"),
    ("Сжатый FASTQ (.gz)", "*.fastq.gz *.fq.gz"),
    ("Все файлы", "*.*"),
]

BG = "#F1F5F9"
CARD = "#FFFFFF"
BORDER = "#CBD5E1"
TEXT = "#0F172A"
MUTED = "#475569"
ACCENT = "#0284C7"
ACCENT_HOVER = "#0369A1"
BASE_COLORS = {"A": "#16A34A", "C": "#2563EB", "G": "#D97706", "T": "#DC2626", "N": "#64748B"}


def is_supported_fastq(filepath: str) -> bool:
    """Проверяет, имеет ли файл допустимое расширение FASTQ."""
    return str(filepath).strip().lower().endswith(SUPPORTED_EXTENSIONS)


def parse_drop_paths(raw_data: str) -> list[str]:
    """Разбирает строку с путями из события Drag & Drop (поддерживает {} и file://)."""
    if not raw_data:
        return []
    tokens = re.findall(r"\{([^}]*)\}|(\S+)", raw_data.strip())
    paths = []
    for braced, plain in tokens:
        item = (braced or plain).strip()
        if item.startswith("file://"):
            item = unquote(urlparse(item).path)
        if item:
            paths.append(item)
    return paths


def summarize_stats(stats) -> dict:
    """Считает краткую сводку по объекту FastqStats."""
    if not stats or stats.n_reads == 0:
        return {"n_reads": 0, "min_len": 0, "max_len": 0, "mean_len": 0.0, "mean_qual": 0.0, "gc_percent": 0.0}

    lengths = stats.length_counts
    total_bp = sum(length * count for length, count in lengths.items())
    quals = stats.mean_quality
    mean_qual = sum(quals) / len(quals) if quals else 0.0
    gc_count = sum(stats._b_counts["G"]) + sum(stats._b_counts["C"])
    total_bases = sum(stats._q_counts)
    return {
        "n_reads": stats.n_reads,
        "min_len": min(lengths),
        "max_len": max(lengths),
        "mean_len": total_bp / stats.n_reads,
        "mean_qual": mean_qual,
        "gc_percent": (gc_count / total_bases * 100) if total_bases else 0.0,
    }


def center_window(win, width: int, height: int):
    """Центрирует окно на экране."""
    win.update_idletasks()
    x = max((win.winfo_screenwidth() - width) // 2, 0)
    y = max((win.winfo_screenheight() - height) // 2, 0)
    win.geometry(f"{width}x{height}+{x}+{y}")


def _style_ax(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", linestyle="--", alpha=0.45, color="#94A3B8")


def draw_quality_ax(ax, stats):
    """Рисует график среднего качества Phred по позициям с цветовыми зонами FastQC."""
    quals = stats.mean_quality
    positions = list(range(1, len(quals) + 1))
    ymax = max(42, (max(quals) + 3) if quals else 42)
    ax.axhspan(0, 20, color="#FEE2E2", alpha=0.55)
    ax.axhspan(20, 28, color="#FEF3C7", alpha=0.55)
    ax.axhspan(28, ymax, color="#DCFCE7", alpha=0.55)
    ax.plot(positions, quals, color=ACCENT, linewidth=2.2, marker="o", markersize=3.5)
    ax.set_ylim(0, ymax)
    ax.set_xlim(0.5, max(len(positions), 1) + 0.5)
    ax.set_title("Per base sequence quality", fontsize=11, fontweight="bold", pad=8)
    ax.set_xlabel("Позиция в риде (bp)")
    ax.set_ylabel("Качество (Phred)")
    _style_ax(ax)


def draw_content_ax(ax, stats):
    """Рисует процентное содержание нуклеотидов A, C, G, T, N по позициям."""
    content = stats.base_content
    for base in "ACGTN":
        ax.plot(content.index, content[base], label=base, color=BASE_COLORS[base], linewidth=1.9)
    ax.set_ylim(0, 100)
    ax.set_title("Per base sequence content", fontsize=11, fontweight="bold", pad=8)
    ax.set_xlabel("Позиция в риде (bp)")
    ax.set_ylabel("Нуклеотид, %")
    ax.legend(loc="upper right", ncol=5, frameon=True, facecolor="white", edgecolor="#E2E8F0", fontsize=9)
    _style_ax(ax)


def draw_length_ax(ax, stats):
    """Рисует распределение длин ридов."""
    lengths = sorted(stats.length_counts)
    counts = [stats.length_counts[l] for l in lengths]
    if len(lengths) <= 15:
        x = list(range(len(lengths)))
        bars = ax.bar(x, counts, color="#0EA5E9", width=0.55)
        ax.set_xticks(x)
        ax.set_xticklabels([str(l) for l in lengths])
        if counts:
            ax.set_ylim(0, max(counts) * 1.18)
            for bar, count in zip(bars, counts):
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height(),
                    str(count),
                    ha="center",
                    va="bottom",
                    fontsize=9,
                    color=TEXT,
                )
    else:
        ax.bar(lengths, counts, color="#0EA5E9")
    ax.set_title("Sequence length distribution", fontsize=11, fontweight="bold", pad=8)
    ax.set_xlabel("Длина рида (bp)")
    ax.set_ylabel("Количество ридов")
    _style_ax(ax)


_BaseTk = TkinterDnD.Tk if HAS_DND else tk.Tk


class FastqAnalyzerApp(_BaseTk):
    """Окно анализатора FASTQ (урезанный FastQC)."""

    def __init__(self, initial_file: str | None = None):
        super().__init__()
        self.title("Урезанный FastQC — biotools")
        self.configure(bg=BG)
        self.minsize(840, 560)
        center_window(self, 1000, 670)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self.current_file: str | None = None
        self.current_stats = None
        self._tab_widgets: list[tk.Widget] = []

        self._setup_styles()
        self._build_ui()

        if initial_file:
            self.after(50, lambda: self.load_file(initial_file))

    def _setup_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure("TNotebook.Tab", padding=(12, 6), font=("DejaVu Sans", 10))
        style.map("TNotebook.Tab", background=[("selected", CARD)], foreground=[("selected", ACCENT)])

    def _build_ui(self):
        top = tk.Frame(self, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        top.pack(fill="x", padx=14, pady=(12, 8))

        btn_box = tk.Frame(top, bg=CARD)
        btn_box.pack(side="right", padx=14, pady=12)

        self.open_btn = tk.Button(
            btn_box,
            text="Открыть FASTQ...",
            command=self.open_file_dialog,
            bg=ACCENT,
            fg="white",
            activebackground=ACCENT_HOVER,
            activeforeground="white",
            relief="flat",
            padx=14,
            pady=7,
            font=("DejaVu Sans", 10, "bold"),
            cursor="hand2",
        )
        self.open_btn.pack(side="left", padx=(0, 8))

        self.save_btn = tk.Button(
            btn_box,
            text="Сохранить PNG",
            command=self.save_plots,
            bg="#E2E8F0",
            fg=TEXT,
            activebackground="#CBD5E1",
            relief="flat",
            padx=12,
            pady=7,
            font=("DejaVu Sans", 10),
            state="disabled",
            cursor="hand2",
        )
        self.save_btn.pack(side="left")

        title_box = tk.Frame(top, bg=CARD)
        title_box.pack(side="left", fill="x", expand=True, padx=14, pady=10)
        tk.Label(title_box, text="Урезанный FastQC", bg=CARD, fg=TEXT, font=("DejaVu Sans", 14, "bold")).pack(anchor="w")
        tk.Label(
            title_box,
            text="Анализ качества и состава (.fastq, .fq, .fastq.gz)",
            bg=CARD,
            fg=MUTED,
            font=("DejaVu Sans", 9),
        ).pack(anchor="w", pady=(2, 0))

        hint = (
            "Перетащите FASTQ-файл сюда или нажмите для выбора"
            if HAS_DND
            else "Нажмите сюда или «Открыть FASTQ...», чтобы выбрать файл"
        )
        self.drop_var = tk.StringVar(value=hint)
        self.drop_frame = tk.Frame(self, bg="#E0F2FE", highlightbackground="#7DD3FC", highlightthickness=1)
        self.drop_frame.pack(fill="x", padx=14, pady=(0, 8))
        self.drop_label = tk.Label(
            self.drop_frame,
            textvariable=self.drop_var,
            bg="#E0F2FE",
            fg="#0369A1",
            font=("DejaVu Sans", 10),
            pady=8,
            cursor="hand2",
        )
        self.drop_label.pack(fill="x")
        self.drop_label.bind("<Button-1>", lambda _e: self.open_file_dialog())

        if HAS_DND:
            for widget in (self, self.drop_frame, self.drop_label):
                widget.drop_target_register(DND_FILES)
                widget.dnd_bind("<<Drop>>", self._on_drop)

        self.summary_frame = tk.Frame(self, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        self.summary_frame.pack(fill="x", padx=14, pady=(0, 8))
        self.summary_vars = {}
        metrics = [
            ("reads", "Ридов"),
            ("length", "Длина (bp)"),
            ("quality", "Ср. Phred"),
            ("gc", "GC-состав"),
        ]
        for key, label in metrics:
            cell = tk.Frame(self.summary_frame, bg=CARD)
            cell.pack(side="left", expand=True, fill="x", padx=12, pady=7)
            tk.Label(cell, text=label, bg=CARD, fg=MUTED, font=("DejaVu Sans", 9)).pack(anchor="w")
            var = tk.StringVar(value="—")
            self.summary_vars[key] = var
            tk.Label(cell, textvariable=var, bg=CARD, fg=TEXT, font=("DejaVu Sans", 11, "bold")).pack(anchor="w")

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=14, pady=(0, 12))

        self.tabs = {}
        for key, title in (
            ("quality", "Качество (Phred)"),
            ("content", "Нуклеотиды"),
            ("length", "Длины ридов"),
            ("all", "Все графики"),
        ):
            frame = tk.Frame(self.notebook, bg=CARD)
            self.notebook.add(frame, text=title)
            self.tabs[key] = frame

        self._show_empty_placeholder()

    def _clear_tabs(self):
        for widget in self._tab_widgets:
            widget.destroy()
        self._tab_widgets.clear()

    def _show_empty_placeholder(self):
        self._clear_tabs()
        for frame in self.tabs.values():
            lbl = tk.Label(
                frame,
                text="Файл не выбран.\n\nНажмите «Открыть FASTQ...» и выберите файл .fastq, .fq или .fastq.gz",
                bg=CARD,
                fg=MUTED,
                font=("DejaVu Sans", 11),
                justify="center",
            )
            lbl.pack(expand=True)
            self._tab_widgets.append(lbl)

    def open_file_dialog(self):
        """Открывает системный диалог выбора FASTQ-файла с фильтром форматов."""
        initial_dir = os.path.dirname(self.current_file) if self.current_file else (
            os.path.join(os.getcwd(), "data") if os.path.isdir("data") else os.getcwd()
        )
        filepath = filedialog.askopenfilename(
            parent=self,
            title="Выберите FASTQ-файл",
            initialdir=initial_dir,
            filetypes=FASTQ_FILETYPES,
        )
        if filepath:
            self.load_file(filepath)

    def _on_drop(self, event):
        paths = parse_drop_paths(event.data)
        if paths:
            self.load_file(paths[0])

    def load_file(self, filepath: str):
        """Читает FASTQ через FastqReader, обновляет сводку и перерисовывает графики."""
        if not os.path.isfile(filepath):
            messagebox.showerror("Файл не найден", f"Не удалось найти файл:\n{filepath}", parent=self)
            return
        if not is_supported_fastq(filepath):
            messagebox.showwarning(
                "Неподдерживаемый формат",
                "Выберите файл формата FASTQ (.fastq, .fq, .fastq.gz или .fq.gz).",
                parent=self,
            )
            return

        self.config(cursor="watch")
        self.update_idletasks()
        try:
            with FastqReader(filepath) as reader:
                stats = reader.compute_stats()
        except (ValueError, OSError) as exc:
            messagebox.showerror("Ошибка чтения FASTQ", f"Не удалось прочитать файл:\n{exc}", parent=self)
            return
        finally:
            self.config(cursor="")

        if stats.n_reads == 0:
            messagebox.showwarning("Пустой файл", "В выбранном FASTQ-файле не найдено ни одного рида.", parent=self)
            return

        self.current_file = filepath
        self.current_stats = stats
        self.drop_var.set(f"Открыт файл: {filepath}")
        self.save_btn.config(state="normal")
        self._update_summary(stats)
        self._render_plots(stats)

    def _update_summary(self, stats):
        info = summarize_stats(stats)
        len_text = (
            f"{info['min_len']}"
            if info["min_len"] == info["max_len"]
            else f"{info['min_len']}–{info['max_len']} (ср. {info['mean_len']:.1f})"
        )
        self.summary_vars["reads"].set(f"{info['n_reads']:,}".replace(",", " "))
        self.summary_vars["length"].set(len_text)
        self.summary_vars["quality"].set(f"{info['mean_qual']:.1f}")
        self.summary_vars["gc"].set(f"{info['gc_percent']:.1f}%")

    def _embed_figure(self, parent: tk.Frame, fig: Figure):
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        toolbar = NavigationToolbar2Tk(canvas, parent, pack_toolbar=False)
        toolbar.update()
        toolbar.pack(side="bottom", fill="x")
        widget = canvas.get_tk_widget()
        widget.pack(side="top", fill="both", expand=True)
        self._tab_widgets.extend([widget, toolbar])

    def _render_plots(self, stats):
        self._clear_tabs()

        for tab_key, drawer in (
            ("quality", draw_quality_ax),
            ("content", draw_content_ax),
            ("length", draw_length_ax),
        ):
            fig = Figure(figsize=(8.8, 4.6), dpi=100, facecolor=CARD)
            ax = fig.add_subplot(111)
            drawer(ax, stats)
            fig.tight_layout()
            self._embed_figure(self.tabs[tab_key], fig)

        fig_all = Figure(figsize=(9.5, 5.8), dpi=95, facecolor=CARD)
        gs = GridSpec(2, 2, figure=fig_all, height_ratios=[1, 0.95])
        draw_quality_ax(fig_all.add_subplot(gs[0, 0]), stats)
        draw_content_ax(fig_all.add_subplot(gs[0, 1]), stats)
        draw_length_ax(fig_all.add_subplot(gs[1, :]), stats)
        fig_all.tight_layout(pad=1.6)
        self._embed_figure(self.tabs["all"], fig_all)

    def save_plots(self):
        """Сохраняет 3 PNG-графика методом FastqReader.plot_all."""
        if not self.current_file:
            return
        initial_dir = os.path.join(os.getcwd(), "plots") if os.path.isdir("plots") else os.getcwd()
        out_dir = filedialog.askdirectory(parent=self, title="Папка для сохранения графиков", initialdir=initial_dir)
        if not out_dir:
            return
        try:
            with FastqReader(self.current_file) as reader:
                reader.plot_all(out_dir)
        except Exception as exc:
            messagebox.showerror("Ошибка сохранения", f"Не удалось сохранить графики:\n{exc}", parent=self)
            return
        messagebox.showinfo("Готово", f"Графики сохранены в папку:\n{out_dir}", parent=self)

    def _on_close(self):
        self.destroy()


def launch_fastq_gui(initial_file: str | None = None):
    """Запускает графический интерфейс анализатора FASTQ."""
    app = FastqAnalyzerApp(initial_file=initial_file)
    app.mainloop()


if __name__ == "__main__":
    arg_file = sys.argv[1] if len(sys.argv) > 1 else None
    launch_fastq_gui(initial_file=arg_file)