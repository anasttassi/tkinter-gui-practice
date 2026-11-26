"""
Задание 18.1.2. Формы учёта-отчёта (Пациенты и ИМТ).
Запуск: python patients_app.py
"""

import json
import os
import random
import tkinter as tk
from tkinter import messagebox, ttk


DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "patients.json")
GENDERS = ("Мужской", "Женский", "Не определён")
GENDER_COLORS = {"Мужской": "#0284C7", "Женский": "#EC4899", "Не определён": "#8B5CF6"}

FONT = "DejaVu Sans"
BG = "#F1F5F9"
CARD_BG = "#FFFFFF"
BORDER = "#CBD5E1"
TEXT = "#0F172A"
MUTED = "#64748B"


def calculate_bmi(weight_kg, height_cm):
    """Вычисляет ИМТ с округлением до 2 знаков."""
    if height_cm <= 0 or weight_kg <= 0:
        raise ValueError("Рост и вес должны быть больше нуля.")
    return round(weight_kg / ((height_cm / 100.0) ** 2), 2)


def normalize_gender(value):
    """Приводит значение пола к одному из 3 стандартных вариантов."""
    cleaned = " ".join(str(value).strip().split()).lower()
    mapping = {
        "мужской": "Мужской",
        "женский": "Женский",
        "не определён": "Не определён",
        "не определен": "Не определён",
    }
    return mapping.get(cleaned, str(value).strip())


def format_full_name(last_name, first_name, middle_name=""):
    """Собирает ФИО в одну строку (отчество добавляется при наличии)."""
    return " ".join(part for part in (last_name, first_name, middle_name) if part)


def validate_name_part(value, label, required=True):
    """Проверяет фамилию, имя или отчество (только буквы и дефис)."""
    cleaned = " ".join(str(value).strip().split())
    if not cleaned:
        if required:
            raise ValueError(f"Поле «{label}» обязательно для заполнения.")
        return ""
    if len(cleaned) < 2:
        raise ValueError(f"Поле «{label}» должно содержать минимум 2 символа.")
    if cleaned.startswith("-") or cleaned.endswith("-") or "--" in cleaned:
        raise ValueError(f"Поле «{label}» заполнено некорректно.")
    if not all(ch.isalpha() or ch == "-" for ch in cleaned):
        raise ValueError(f"Поле «{label}» должно содержать только буквы.")
    return "-".join(part[0].upper() + part[1:] for part in cleaned.split("-"))


def split_legacy_full_name(full_name):
    """Разбирает старую строку ФИО на (фамилия, имя, отчество) для совместимости."""
    parts = " ".join(str(full_name).strip().split()).split()
    if len(parts) >= 3:
        suffixes = ("ович", "евич", "ич", "овна", "евна", "ична", "инична")
        if parts[1].lower().endswith(suffixes) and not parts[2].lower().endswith(suffixes):
            return " ".join(parts[2:]), parts[0], parts[1]
        return parts[0], parts[1], " ".join(parts[2:])
    if len(parts) == 2:
        return parts[0], parts[1], ""
    return (parts[0], "", "") if parts else ("", "", "")


def _parse_float(value, min_val, max_val, label, unit):
    """Проверяет вещественное число (поддерживает и точку, и запятую)."""
    try:
        num = float(str(value).strip().replace(",", "."))
    except ValueError:
        raise ValueError(f"{label} должен быть числом (в {unit}).")
    if not (min_val <= num <= max_val):
        raise ValueError(f"{label} должен быть от {min_val} до {max_val} {unit}.")
    return round(num, 1)


def validate_patient_data(last_name, first_name, middle_name, age_str, gender, height_str, weight_str):
    """Проверяет все поля формы и возвращает словарь пациента с ИМТ."""
    last = validate_name_part(last_name, "Фамилия", required=True)
    first = validate_name_part(first_name, "Имя", required=True)
    middle = validate_name_part(middle_name, "Отчество", required=False)

    norm_gender = normalize_gender(gender)
    if norm_gender not in GENDERS:
        raise ValueError("Выберите пол из списка.")

    try:
        age = int(str(age_str).strip())
    except ValueError:
        raise ValueError("Возраст должен быть целым числом.")
    if not (0 <= age <= 120):
        raise ValueError("Возраст должен быть от 0 до 120 лет.")

    height = _parse_float(height_str, 40, 250, "Рост", "см")
    weight = _parse_float(weight_str, 2, 350, "Вес", "кг")

    return {
        "last_name": last,
        "first_name": first,
        "middle_name": middle,
        "full_name": format_full_name(last, first, middle),
        "age": age,
        "gender": norm_gender,
        "height_cm": height,
        "weight_kg": weight,
        "bmi": calculate_bmi(weight, height),
    }


def load_patients(file_path=DATA_FILE):
    """Загружает пациентов из JSON-файла при старте программы."""
    if not os.path.exists(file_path):
        return []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return []
    if not isinstance(data, list):
        return []

    patients = []
    for item in data:
        if not isinstance(item, dict):
            continue
        if "last_name" in item or "first_name" in item:
            last, first, middle = item.get("last_name", ""), item.get("first_name", ""), item.get("middle_name", "")
        else:
            last, first, middle = split_legacy_full_name(item.get("full_name", ""))
        try:
            patients.append(validate_patient_data(
                last, first, middle, item.get("age", ""), item.get("gender", ""),
                item.get("height_cm", ""), item.get("weight_kg", ""),
            ))
        except ValueError:
            continue
    return patients


def save_patients(patients, file_path=DATA_FILE):
    """Сохраняет список пациентов в JSON-файл."""
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(patients, f, ensure_ascii=False, indent=2)


def generate_sample_patients(count=20):
    """Генерирует тестовую выборку через faker (или встроенный random)."""
    try:
        from faker import Faker
        fake = Faker("ru_RU")
    except ImportError:
        fake = None

    fallback_male = [("Иванов", "Алексей", "Петрович"), ("Смирнов", "Дмитрий", "Сергеевич"),
                     ("Кузнецов", "Илья", "Андреевич"), ("Соколов", "Артём", "Николаевич")]
    fallback_female = [("Петрова", "Анна", "Сергеевна"), ("Сидорова", "Мария", "Алексеевна"),
                       ("Морозова", "Елена", "Дмитриевна"), ("Козлова", "Ольга", "Павловна")]

    sample = []
    for _ in range(count):
        gender = random.choices(GENDERS, weights=[45, 45, 10], k=1)[0]
        is_male_name = gender == "Мужской" or (gender == "Не определён" and random.random() < 0.5)

        if fake:
            last = fake.last_name_male() if is_male_name else fake.last_name_female()
            first = fake.first_name_male() if is_male_name else fake.first_name_female()
            middle = fake.middle_name_male() if is_male_name else fake.middle_name_female()
        else:
            last, first, middle = random.choice(fallback_male if is_male_name else fallback_female)

        ranges = {"Мужской": (165, 195, 62, 108), "Женский": (152, 180, 48, 88)}.get(
            gender, (158, 188, 52, 96)
        )
        height = round(random.uniform(ranges[0], ranges[1]), 1)
        weight = round(random.uniform(ranges[2], ranges[3]), 1)

        sample.append({
            "last_name": last,
            "first_name": first,
            "middle_name": middle,
            "full_name": format_full_name(last, first, middle),
            "age": random.randint(18, 80),
            "gender": gender,
            "height_cm": height,
            "weight_kg": weight,
            "bmi": calculate_bmi(weight, height),
        })
    return sample


def center_window(win, parent, width, height):
    """Центрирует дочернее окно относительно главного окна."""
    parent.update_idletasks()
    x = parent.winfo_x() + (parent.winfo_width() - width) // 2
    y = parent.winfo_y() + (parent.winfo_height() - height) // 2
    win.geometry(f"{width}x{height}+{max(0, x)}+{max(0, y)}")


class PatientDialog(tk.Toplevel):
    """Модальное окно добавления и редактирования пациента."""

    def __init__(self, parent, title, on_save, initial_data=None):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.configure(bg=CARD_BG)
        self.transient(parent)
        self.grab_set()
        center_window(self, parent, 510, 455)
        self.on_save = on_save

        if initial_data:
            if "last_name" in initial_data or "first_name" in initial_data:
                last, first, middle = (
                    initial_data.get("last_name", ""),
                    initial_data.get("first_name", ""),
                    initial_data.get("middle_name", ""),
                )
            else:
                last, first, middle = split_legacy_full_name(initial_data.get("full_name", ""))
        else:
            last = first = middle = ""

        self.vars = {
            "last": tk.StringVar(value=last),
            "first": tk.StringVar(value=first),
            "middle": tk.StringVar(value=middle),
            "age": tk.StringVar(value=str(initial_data["age"]) if initial_data else ""),
            "gender": tk.StringVar(value=initial_data["gender"] if initial_data else GENDERS[0]),
            "height": tk.StringVar(value=str(initial_data["height_cm"]) if initial_data else ""),
            "weight": tk.StringVar(value=str(initial_data["weight_kg"]) if initial_data else ""),
        }

        form = tk.Frame(self, bg=CARD_BG, padx=22, pady=18)
        form.pack(fill=tk.BOTH, expand=True)
        form.columnconfigure(1, weight=1)

        fields = [
            ("Фамилия*:", "last", "entry"),
            ("Имя*:", "first", "entry"),
            ("Отчество (при наличии):", "middle", "entry"),
            ("Возраст (лет)*:", "age", "entry"),
            ("Пол*:", "gender", "combo"),
            ("Рост (см)*:", "height", "entry"),
            ("Вес (кг)*:", "weight", "entry"),
        ]

        first_entry = None
        for row, (label, key, kind) in enumerate(fields):
            tk.Label(form, text=label, font=(FONT, 10), bg=CARD_BG, fg=TEXT, anchor="w").grid(
                row=row, column=0, sticky="w", pady=6, padx=(0, 12)
            )
            if kind == "combo":
                widget = ttk.Combobox(form, textvariable=self.vars[key], values=GENDERS,
                                      state="readonly", font=(FONT, 10))
            else:
                widget = tk.Entry(form, textvariable=self.vars[key], font=(FONT, 10), bg="#F8FAFC",
                                  relief=tk.FLAT, highlightthickness=1, highlightbackground=BORDER,
                                  highlightcolor="#0284C7")
            widget.grid(row=row, column=1, sticky="ew", pady=6, ipady=4)
            first_entry = first_entry or widget

        tk.Label(form, text="* — обязательные поля (отчество можно не указывать)",
                 font=(FONT, 8), bg=CARD_BG, fg=MUTED).grid(
            row=len(fields), column=0, columnspan=2, sticky="w", pady=(4, 0)
        )

        self.error_label = tk.Label(form, text="", font=(FONT, 9), bg=CARD_BG, fg="#DC2626",
                                    wraplength=440, justify=tk.LEFT)
        self.error_label.grid(row=len(fields) + 1, column=0, columnspan=2, sticky="w", pady=(6, 4))

        btns = tk.Frame(form, bg=CARD_BG)
        btns.grid(row=len(fields) + 2, column=0, columnspan=2, sticky="e", pady=(8, 0))
        tk.Button(btns, text="Отмена", font=(FONT, 10), bg="#E2E8F0", fg=TEXT,
                  activebackground="#CBD5E1", relief=tk.FLAT, padx=14, pady=6, cursor="hand2",
                  command=self.destroy).pack(side=tk.LEFT, padx=(0, 8))
        tk.Button(btns, text="Сохранить", font=(FONT, 10, "bold"), bg="#0284C7", fg="#FFFFFF",
                  activebackground="#0369A1", activeforeground="#FFFFFF", relief=tk.FLAT,
                  padx=16, pady=6, cursor="hand2", command=self.submit).pack(side=tk.LEFT)

        self.bind("<Return>", lambda _e: self.submit())
        self.bind("<Escape>", lambda _e: self.destroy())
        first_entry.focus()

    def submit(self):
        try:
            patient = validate_patient_data(
                self.vars["last"].get(), self.vars["first"].get(), self.vars["middle"].get(),
                self.vars["age"].get(), self.vars["gender"].get(),
                self.vars["height"].get(), self.vars["weight"].get(),
            )
        except ValueError as err:
            self.error_label.configure(text=str(err))
            return
        self.on_save(patient)
        self.destroy()


class PatientsApp:
    """Главное окно учёта пациентов и просмотра статистики."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Учёт пациентов и статистика ИМТ")
        self.root.geometry("1100x600")
        self.root.minsize(940, 480)
        self.root.configure(bg=BG)

        self.patients = load_patients()
        self.sort_state = {}

        self.configure_styles()
        self.create_toolbar()
        self.create_table()
        self.create_status_bar()
        self.refresh_view()

    def configure_styles(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Treeview", font=(FONT, 10), rowheight=29, background=CARD_BG,
                        fieldbackground=CARD_BG, bordercolor=BORDER)
        style.configure("Treeview.Heading", font=(FONT, 10, "bold"), background="#E2E8F0",
                        foreground=TEXT, relief="flat")
        style.map("Treeview.Heading", background=[("active", "#CBD5E1")])
        style.map("Treeview", background=[("selected", "#BAE6FD")], foreground=[("selected", TEXT)])

    def create_toolbar(self):
        bar = tk.Frame(self.root, bg=CARD_BG, highlightthickness=1, highlightbackground=BORDER,
                       padx=16, pady=12)
        bar.pack(fill=tk.X, padx=16, pady=(16, 10))

        tk.Label(bar, text="База пациентов", font=(FONT, 13, "bold"),
                 bg=CARD_BG, fg=TEXT, anchor="w").pack(fill=tk.X, pady=(0, 8))

        row = tk.Frame(bar, bg=CARD_BG)
        row.pack(fill=tk.X)

        buttons = [
            ("Добавить", "#0F766E", "#FFFFFF", "#0D5E58", self.open_add_dialog),
            ("Редактировать", "#E2E8F0", TEXT, "#CBD5E1", self.open_edit_dialog),
            ("Удалить", "#FEE2E2", "#B91C1C", "#FECACA", self.delete_selected),
            ("Примеры (+20)", "#E2E8F0", TEXT, "#CBD5E1", self.fill_sample_data),
        ]
        for text, bg, fg, abg, cmd in buttons:
            tk.Button(row, text=text, font=(FONT, 10, "bold" if fg == "#FFFFFF" else "normal"),
                      bg=bg, fg=fg, activebackground=abg, activeforeground=fg,
                      relief=tk.FLAT, padx=12, pady=6, cursor="hand2",
                      command=cmd).pack(side=tk.LEFT, padx=(0, 8))

        tk.Button(row, text="Статистика", font=(FONT, 10, "bold"), bg="#0284C7", fg="#FFFFFF",
                  activebackground="#0369A1", activeforeground="#FFFFFF", relief=tk.FLAT,
                  padx=16, pady=6, cursor="hand2", command=self.show_statistics).pack(side=tk.RIGHT)

    def create_table(self):
        frame = tk.Frame(self.root, bg=CARD_BG, highlightthickness=1, highlightbackground=BORDER)
        frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 8))

        cols = ("full_name", "age", "gender", "height_cm", "weight_kg", "bmi")
        self.tree = ttk.Treeview(frame, columns=cols, show="headings", selectmode="browse")
        self.tree.tag_configure("even", background="#FFFFFF")
        self.tree.tag_configure("odd", background="#F8FAFC")

        headings = {
            "full_name": ("ФИО", 420, tk.W),
            "age": ("Возраст", 90, tk.CENTER),
            "gender": ("Пол", 130, tk.CENTER),
            "height_cm": ("Рост (см)", 110, tk.CENTER),
            "weight_kg": ("Вес (кг)", 110, tk.CENTER),
            "bmi": ("ИМТ", 100, tk.CENTER),
        }
        for col, (title, width, anchor) in headings.items():
            self.tree.heading(col, text=title, command=lambda c=col: self.sort_by(c))
            self.tree.column(col, width=width, anchor=anchor)

        scroll = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.bind("<Double-1>", lambda _e: self.open_edit_dialog())

    def create_status_bar(self):
        self.status_label = tk.Label(self.root, text="", font=(FONT, 9), bg=BG, fg=MUTED, anchor="w")
        self.status_label.pack(fill=tk.X, padx=18, pady=(0, 12))

    def refresh_view(self):
        self.tree.delete(*self.tree.get_children())
        for idx, p in enumerate(self.patients):
            tag = "even" if idx % 2 == 0 else "odd"
            self.tree.insert("", tk.END, iid=str(idx), tags=(tag,), values=(
                p["full_name"], p["age"], p["gender"], p["height_cm"], p["weight_kg"], f"{p['bmi']:.2f}"
            ))

        self.status_label.configure(
            text=f"Всего пациентов: {len(self.patients)} | Нажмите на заголовок столбца для сортировки | Файл: {os.path.basename(DATA_FILE)}"
        )

    def sort_by(self, col):
        reverse = not self.sort_state.get(col, False)
        self.sort_state[col] = reverse
        self.patients.sort(
            key=lambda p: p[col].lower() if isinstance(p[col], str) else p[col],
            reverse=reverse,
        )
        self.refresh_view()

    def get_selected_index(self):
        sel = self.tree.selection()
        return int(sel[0]) if sel else None

    def open_add_dialog(self):
        def add(patient):
            self.patients.append(patient)
            save_patients(self.patients)
            self.refresh_view()
        PatientDialog(self.root, "Добавить пациента", on_save=add)

    def open_edit_dialog(self):
        idx = self.get_selected_index()
        if idx is None:
            messagebox.showinfo("Выбор пациента", "Сначала выберите строку с пациентом в таблице.")
            return
        def update(patient):
            self.patients[idx] = patient
            save_patients(self.patients)
            self.refresh_view()
        PatientDialog(self.root, "Редактировать пациента", on_save=update, initial_data=self.patients[idx])

    def delete_selected(self):
        idx = self.get_selected_index()
        if idx is None:
            messagebox.showinfo("Удаление", "Сначала выберите пациента в таблице.")
            return
        if messagebox.askyesno("Подтверждение", f"Удалить запись: {self.patients[idx]['full_name']}?"):
            self.patients.pop(idx)
            save_patients(self.patients)
            self.refresh_view()

    def fill_sample_data(self):
        self.patients.extend(generate_sample_patients(20))
        save_patients(self.patients)
        self.refresh_view()

    def show_statistics(self):
        if not self.patients:
            messagebox.showinfo("Статистика", "Нет данных для графиков. Добавьте пациентов или нажмите «Примеры (+20)».")
            return
        try:
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            from matplotlib.figure import Figure
        except ImportError:
            messagebox.showerror("Не найден matplotlib", "Установите matplotlib:\npip install matplotlib")
            return

        win = tk.Toplevel(self.root)
        win.title("Сводная статистика пациентов")
        win.configure(bg="#F8FAFC")
        center_window(win, self.root, 1020, 720)

        fig = Figure(figsize=(9.8, 6.8), dpi=100, facecolor="#F8FAFC")
        grouped = {g: [p for p in self.patients if p["gender"] == g] for g in GENDERS}

        # 1. Распределение по полу
        ax1 = fig.add_subplot(2, 2, 1)
        counts = [len(grouped[g]) for g in GENDERS]
        bars = ax1.bar(GENDERS, counts, color=[GENDER_COLORS[g] for g in GENDERS], width=0.52)
        ax1.set_title("Распределение пациентов по полу", fontweight="bold")
        ax1.set_ylabel("Количество")
        ax1.tick_params(axis="x", labelsize=9)
        ax1.set_ylim(0, max(counts) + max(1.0, max(counts) * 0.18))
        for bar, cnt in zip(bars, counts):
            ax1.text(bar.get_x() + bar.get_width() / 2, cnt + 0.1, str(cnt),
                     ha="center", va="bottom", fontsize=9)

        # 2. Распределение по возрасту
        ax2 = fig.add_subplot(2, 2, 2)
        ages = [p["age"] for p in self.patients]
        ax2.hist(ages, bins=min(10, max(3, len(set(ages)))), color="#0F766E", edgecolor="#FFFFFF")
        ax2.set_title("Распределение пациентов по возрасту", fontweight="bold")
        ax2.set_xlabel("Возраст (лет)")
        ax2.set_ylabel("Количество")

        # 3. Распределение ИМТ с учётом пола
        ax3 = fig.add_subplot(2, 2, 3)
        groups = [(g, [p["bmi"] for p in grouped[g]]) for g in GENDERS if grouped[g]]
        ax3.hist([b for _, b in groups], bins=8, label=[g for g, _ in groups],
                 color=[GENDER_COLORS[g] for g, _ in groups], edgecolor="#FFFFFF")
        ax3.set_title("Распределение ИМТ с учётом пола", fontweight="bold")
        ax3.set_xlabel("ИМТ")
        ax3.set_ylabel("Количество")
        ax3.legend(fontsize=8, frameon=False)

        # 4. Зависимость ИМТ от возраста
        ax4 = fig.add_subplot(2, 2, 4)
        for g in GENDERS:
            if grouped[g]:
                ax4.scatter([p["age"] for p in grouped[g]], [p["bmi"] for p in grouped[g]],
                            color=GENDER_COLORS[g], label=g, alpha=0.82)
        ax4.set_title("Зависимость ИМТ от возраста", fontweight="bold")
        ax4.set_xlabel("Возраст (лет)")
        ax4.set_ylabel("ИМТ")
        ax4.legend(fontsize=8, frameon=False)

        for ax in (ax1, ax2, ax3, ax4):
            ax.set_facecolor("#FFFFFF")
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.grid(axis="both" if ax is ax4 else "y", linestyle="--", alpha=0.35)

        fig.tight_layout(pad=2.2)
        canvas = FigureCanvasTkAgg(fig, master=win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    PatientsApp().run()