import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json
import os
from datetime import datetime

API_URL = "https://api.exchangerate-api.com/v4/latest/"  # Бесплатный API (без ключа)
HISTORY_FILE = "history.json"

class CurrencyConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("Currency Converter")
        self.root.geometry("600x500")
        self.root.resizable(False, False)

        # Загрузка списка валют
        self.currencies = self.get_currencies()

        # Создание интерфейса
        self.create_widgets()

        # Загрузка истории
        self.load_history()

    def get_currencies(self):
        """Получение списка доступных валют из API"""
        try:
            response = requests.get(API_URL + "USD")
            data = response.json()
            return sorted(data['rates'].keys())
        except:
            messagebox.showerror("Error", "Failed to fetch currency list. Check your internet.")
            return ["USD", "EUR", "RUB", "GBP", "JPY"]

    def create_widgets(self):
        # Frame ввода
        input_frame = ttk.LabelFrame(self.root, text="Currency Conversion", padding=10)
        input_frame.pack(fill="x", padx=10, pady=10)

        # Сумма
        ttk.Label(input_frame, text="Amount:").grid(row=0, column=0, sticky="w", pady=5)
        self.amount_entry = ttk.Entry(input_frame, width=20)
        self.amount_entry.grid(row=0, column=1, pady=5, padx=5)
        self.amount_entry.bind('<KeyRelease>', self.validate_amount)  # валидация на лету
        self.amount_error = ttk.Label(input_frame, text="", foreground="red")
        self.amount_error.grid(row=0, column=2, sticky="w", padx=5)

        # Из валюты
        ttk.Label(input_frame, text="From Currency:").grid(row=1, column=0, sticky="w", pady=5)
        self.from_currency = ttk.Combobox(input_frame, values=self.currencies, width=20)
        self.from_currency.grid(row=1, column=1, pady=5, padx=5)
        self.from_currency.set("USD")

        # В валюту
        ttk.Label(input_frame, text="To Currency:").grid(row=2, column=0, sticky="w", pady=5)
        self.to_currency = ttk.Combobox(input_frame, values=self.currencies, width=20)
        self.to_currency.grid(row=2, column=1, pady=5, padx=5)
        self.to_currency.set("EUR")

        # Кнопка конвертации
        self.convert_btn = ttk.Button(input_frame, text="Convert", command=self.convert)
        self.convert_btn.grid(row=3, column=0, columnspan=2, pady=10)

        # Результат
        self.result_label = ttk.Label(input_frame, text="", font=("Arial", 12, "bold"))
        self.result_label.grid(row=4, column=0, columnspan=3, pady=5)

        # История
        history_frame = ttk.LabelFrame(self.root, text="Conversion History", padding=10)
        history_frame.pack(fill="both", expand=True, padx=10, pady=10)

        columns = ("Date", "Amount", "From", "To", "Result")
        self.history_tree = ttk.Treeview(history_frame, columns=columns, show="headings", height=12)
        for col in columns:
            self.history_tree.heading(col, text=col)
            self.history_tree.column(col, width=100)

        scrollbar = ttk.Scrollbar(history_frame, orient="vertical", command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=scrollbar.set)
        self.history_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Кнопка очистки истории
        clear_btn = ttk.Button(history_frame, text="Clear History", command=self.clear_history)
        clear_btn.pack(pady=5)

    def validate_amount(self, event=None):
        """Проверка корректности ввода суммы"""
        amount_str = self.amount_entry.get().strip()
        if not amount_str:
            self.amount_error.config(text="")
            return False
        try:
            amount = float(amount_str)
            if amount <= 0:
                self.amount_error.config(text="Amount must be positive")
                return False
            else:
                self.amount_error.config(text="")
                return True
        except ValueError:
            self.amount_error.config(text="Invalid number")
            return False

    def convert(self):
        """Конвертация валюты"""
        if not self.validate_amount():
            messagebox.showwarning("Input Error", "Please enter a valid positive amount.")
            return

        amount = float(self.amount_entry.get())
        from_cur = self.from_currency.get()
        to_cur = self.to_currency.get()

        if from_cur == to_cur:
            result = amount
        else:
            try:
                # Получение курса
                response = requests.get(API_URL + from_cur)
                data = response.json()
                rate = data['rates'].get(to_cur)
                if not rate:
                    messagebox.showerror("Error", f"Currency {to_cur} not found.")
                    return
                result = amount * rate
            except Exception as e:
                messagebox.showerror("API Error", f"Failed to get exchange rate: {e}")
                return

        # Отображение результата
        result_text = f"{amount:.2f} {from_cur} = {result:.2f} {to_cur}"
        self.result_label.config(text=result_text)

        # Сохранение в историю
        self.add_to_history(amount, from_cur, to_cur, result)

    def add_to_history(self, amount, from_cur, to_cur, result):
        """Добавление записи в историю и сохранение в JSON"""
        history_entry = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "amount": amount,
            "from_currency": from_cur,
            "to_currency": to_cur,
            "result": round(result, 4)
        }

        # Загрузка существующей истории
        history = []
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r") as f:
                try:
                    history = json.load(f)
                except:
                    history = []

        history.append(history_entry)

        # Сохранение в файл
        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=4)

        # Обновление таблицы
        self.history_tree.insert("", 0, values=(
            history_entry["date"],
            f"{history_entry['amount']:.2f}",
            history_entry["from_currency"],
            history_entry["to_currency"],
            f"{history_entry['result']:.4f}"
        ))

    def load_history(self):
        """Загрузка истории из JSON при запуске"""
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r") as f:
                try:
                    history = json.load(f)
                    for entry in reversed(history):  # Показываем последние сверху
                        self.history_tree.insert("", "end", values=(
                            entry["date"],
                            f"{entry['amount']:.2f}",
                            entry["from_currency"],
                            entry["to_currency"],
                            f"{entry['result']:.4f}"
                        ))
                except:
                    pass

    def clear_history(self):
        """Очистка истории"""
        if messagebox.askyesno("Clear History", "Are you sure you want to clear history?"):
            self.history_tree.delete(*self.history_tree.get_children())
            if os.path.exists(HISTORY_FILE):
                os.remove(HISTORY_FILE)

if __name__ == "__main__":
    root = tk.Tk()
    app = CurrencyConverter(root)
    root.mainloop()