"""
Задание 18.1.1. Калькулятор на Tkinter.
Запуск: python calculator.py

Поддерживает:
- ввод с клавиатуры и кнопочной панели;
- операции: +, -, *, /, sqrt (квадратный корень);
- валидацию ввода и обработку исключений (деление на 0, корень из < 0).
"""

import math
import tkinter as tk


OPERATORS = {"+", "-", "*", "/"}


def tokenize(expression):
    """Разбивает строку выражения на числа и операторы, проверяя корректность ввода."""
    cleaned = expression.replace(" ", "").replace(",", ".")

    if not cleaned:
        raise ValueError("Введите число или выражение.")

    tokens = []
    index = 0
    length = len(cleaned)
    expect_number = True

    while index < length:
        ch = cleaned[index]

        if expect_number:
            sign = ""
            if ch in "+-":
                sign = ch
                index += 1
                if index >= length:
                    raise ValueError("Выражение не завершено после знака.")
                ch = cleaned[index]

            num_chars = []
            dot_count = 0

            while index < length and (cleaned[index].isdigit() or cleaned[index] == "."):
                current = cleaned[index]
                if current == ".":
                    dot_count += 1
                    if dot_count > 1:
                        raise ValueError("Некорректное число: лишняя десятичная точка.")
                num_chars.append(current)
                index += 1

            num_str = sign + "".join(num_chars)

            if not num_chars or num_chars == ["."]:
                if index < length and cleaned[index] in OPERATORS:
                    raise ValueError("Два знака операции подряд недопустимы.")
                if index < length:
                    raise ValueError(f"Недопустимый символ: '{cleaned[index]}'.")
                raise ValueError("Некорректная запись числа.")

            tokens.append(float(num_str))
            expect_number = False
        else:
            if ch in OPERATORS:
                tokens.append(ch)
                index += 1
                expect_number = True
            else:
                raise ValueError(
                    f"Недопустимый символ '{ch}'. Разрешены только цифры и +, -, *, /."
                )

    if expect_number:
        raise ValueError("Выражение не должно заканчиваться знаком операции.")

    return tokens


def calculate_tokens(tokens):
    """Вычисляет выражение с учётом приоритета: сначала * и /, затем + и -."""
    high_priority = [tokens[0]]
    i = 1
    while i < len(tokens):
        op = tokens[i]
        right = float(tokens[i + 1])

        if op == "*":
            left = float(high_priority.pop())
            high_priority.append(left * right)
        elif op == "/":
            if right == 0:
                raise ZeroDivisionError("Деление на ноль невозможно.")
            left = float(high_priority.pop())
            high_priority.append(left / right)
        else:
            high_priority.append(op)
            high_priority.append(right)

        i += 2

    result = float(high_priority[0])
    i = 1
    while i < len(high_priority):
        op = high_priority[i]
        right = float(high_priority[i + 1])
        if op == "+":
            result += right
        elif op == "-":
            result -= right
        i += 2

    if not math.isfinite(result):
        raise OverflowError("Результат слишком велик для отображения.")

    return result


def evaluate_expression(expression):
    """Проверяет и вычисляет арифметическое выражение."""
    tokens = tokenize(expression)
    return calculate_tokens(tokens)


def calculate_sqrt(expression):
    """Вычисляет квадратный корень из значения (с проверкой на отрицательное число)."""
    value = evaluate_expression(expression)
    if value < 0:
        raise ValueError("Нельзя извлечь квадратный корень из отрицательного числа.")
    return math.sqrt(value)


def format_number(value):
    """Форматирует число: убирает '.0' у целых и лишние нули после точки."""
    if abs(value) < 1e-12:
        value = 0.0

    if abs(value) >= 1e12 or (0 < abs(value) < 1e-6):
        return f"{value:.8g}"

    rounded = round(value, 10)
    if rounded.is_integer():
        return str(int(rounded))
    return f"{rounded:.10f}".rstrip("0").rstrip(".")


class CalculatorApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Калькулятор")
        self.root.geometry("380x500")
        self.root.minsize(340, 460)

        self.bg_color = "#F4F6F9"
        self.panel_color = "#FFFFFF"
        self.text_color = "#1E293B"
        self.muted_color = "#64748B"
        self.digit_bg = "#FFFFFF"
        self.op_bg = "#E2E8F0"
        self.accent_bg = "#0284C7"
        self.clear_bg = "#FEE2E2"
        self.clear_fg = "#B91C1C"
        self.error_fg = "#DC2626"
        self.font_name = "DejaVu Sans"

        self.root.configure(bg=self.bg_color)

        self.create_display()
        self.create_buttons()
        self.bind_keyboard()

    def create_display(self):
        display_frame = tk.Frame(
            self.root,
            bg=self.panel_color,
            bd=1,
            relief=tk.SOLID,
            padx=14,
            pady=14,
        )
        display_frame.pack(fill=tk.X, padx=16, pady=(16, 10))

        tk.Label(
            display_frame,
            text="Введите выражение:",
            font=(self.font_name, 10),
            fg=self.muted_color,
            bg=self.panel_color,
            anchor="w",
        ).pack(fill=tk.X)

        self.input_entry = tk.Entry(
            display_frame,
            font=(self.font_name, 18),
            fg=self.text_color,
            bg="#F8FAFC",
            justify=tk.RIGHT,
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground="#CBD5E1",
            highlightcolor=self.accent_bg,
        )
        self.input_entry.pack(fill=tk.X, pady=(6, 10), ipady=8)
        self.input_entry.focus()

        self.result_label = tk.Label(
            display_frame,
            text="Результат: 0",
            font=(self.font_name, 13, "bold"),
            fg=self.text_color,
            bg=self.panel_color,
            anchor="e",
            wraplength=320,
            justify=tk.RIGHT,
        )
        self.result_label.pack(fill=tk.X)

    def create_buttons(self):
        buttons_frame = tk.Frame(self.root, bg=self.bg_color)
        buttons_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=(4, 16))

        layout = [
            ("C", 0, 0, "clear"), ("DEL", 0, 1, "op"), ("sqrt", 0, 2, "op"), ("/", 0, 3, "op"),
            ("7", 1, 0, "digit"), ("8", 1, 1, "digit"), ("9", 1, 2, "digit"), ("*", 1, 3, "op"),
            ("4", 2, 0, "digit"), ("5", 2, 1, "digit"), ("6", 2, 2, "digit"), ("-", 2, 3, "op"),
            ("1", 3, 0, "digit"), ("2", 3, 1, "digit"), ("3", 3, 2, "digit"), ("+", 3, 3, "op"),
            ("0", 4, 0, "digit"), (".", 4, 1, "digit"), ("=", 4, 2, "accent"),
        ]

        for row in range(5):
            buttons_frame.rowconfigure(row, weight=1, uniform="row")
        for col in range(4):
            buttons_frame.columnconfigure(col, weight=1, uniform="col")

        for text, row, col, kind in layout:
            bg, fg = self.get_button_colors(kind)
            colspan = 2 if text == "=" else 1

            btn = tk.Button(
                buttons_frame,
                text=text,
                font=(self.font_name, 13, "bold" if kind in ("accent", "op") else "normal"),
                bg=bg,
                fg=fg,
                activebackground="#CBD5E1",
                relief=tk.FLAT,
                cursor="hand2",
                command=lambda value=text: self.on_button_click(value),
            )
            btn.grid(
                row=row,
                column=col,
                columnspan=colspan,
                sticky="nsew",
                padx=4,
                pady=4,
            )

    def get_button_colors(self, kind):
        if kind == "accent":
            return self.accent_bg, "#FFFFFF"
        if kind == "clear":
            return self.clear_bg, self.clear_fg
        if kind == "op":
            return self.op_bg, self.text_color
        return self.digit_bg, self.text_color

    def bind_keyboard(self):
        self.root.bind("<Return>", lambda _event: self.calculate())
        self.root.bind("<KP_Enter>", lambda _event: self.calculate())
        self.root.bind("<Escape>", lambda _event: self.clear_all())

    def on_button_click(self, value):
        if value == "C":
            self.clear_all()
        elif value == "DEL":
            self.backspace()
        elif value == "=":
            self.calculate()
        elif value == "sqrt":
            self.calculate_square_root()
        else:
            cursor_pos = self.input_entry.index(tk.INSERT)
            self.input_entry.insert(cursor_pos, value)
            self.input_entry.focus()

    def clear_all(self):
        self.input_entry.delete(0, tk.END)
        self.show_result("Результат: 0")
        self.input_entry.focus()

    def backspace(self):
        cursor_pos = self.input_entry.index(tk.INSERT)
        if cursor_pos > 0:
            self.input_entry.delete(cursor_pos - 1, cursor_pos)
        self.input_entry.focus()

    def calculate(self):
        expression = self.input_entry.get()
        try:
            result = evaluate_expression(expression)
            self.show_result(f"Результат: {format_number(result)}")
        except (ValueError, ZeroDivisionError, OverflowError) as error:
            self.show_error(str(error))
        self.input_entry.focus()

    def calculate_square_root(self):
        expression = self.input_entry.get()
        try:
            result = calculate_sqrt(expression)
            self.show_result(f"sqrt = {format_number(result)}")
        except (ValueError, ZeroDivisionError, OverflowError) as error:
            self.show_error(str(error))
        self.input_entry.focus()

    def show_result(self, text):
        self.result_label.configure(text=text, fg=self.text_color)

    def show_error(self, message):
        self.result_label.configure(text=f"Ошибка: {message}", fg=self.error_fg)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = CalculatorApp()
    app.run()