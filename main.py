import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json
import os

# --- НАСТРОЙКИ ---
API_KEY = "YOUR_API_KEY_HERE" # ЗАМЕНИТЕ ЭТОТ КЛЮЧ НА СВОЙ!
API_URL = "https://v6.exchangerate-api.com/v6/"
HISTORY_FILE = "history.json"
# ------------------

class CurrencyConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Currency Converter")
        self.root.geometry("600x400")

        # Список валют (загружается при старте)
        self.currencies = {}
        self.load_currencies()

        # Создание виджетов
        self.create_widgets()

        # Загрузка истории
        self.history = []
        self.load_history()

    def create_widgets(self):
        # Рамка для ввода данных
        input_frame = ttk.LabelFrame(self.root, text="Конвертация", padding="10")
        input_frame.pack(fill="x", padx=10, pady=5)

        # Валюта "Из"
        ttk.Label(input_frame, text="Из:").grid(row=0, column=0, sticky="w")
        self.from_currency_var = tk.StringVar()
        self.from_currency_combo = ttk.Combobox(input_frame, 
                                                textvariable=self.from_currency_var, 
                                                values=list(self.currencies.keys()), 
                                                state="readonly", 
                                                width=5)
        self.from_currency_combo.current(0) # По умолчанию USD
        self.from_currency_combo.grid(row=0, column=1, padx=5, pady=5)

        # Валюта "В"
        ttk.Label(input_frame, text="В:").grid(row=0, column=2, sticky="e")
        self.to_currency_var = tk.StringVar()
        self.to_currency_combo = ttk.Combobox(input_frame, 
                                              textvariable=self.to_currency_var, 
                                              values=list(self.currencies.keys()), 
                                              state="readonly", 
                                              width=5)
        self.to_currency_combo.current(1) # По умолчанию RUB (если есть)
        self.to_currency_combo.grid(row=0, column=3, padx=5, pady=5)

        # Сумма
        ttk.Label(input_frame, text="Сумма:").grid(row=1, column=0, sticky="w")
        self.amount_var = tk.StringVar()
        self.amount_entry = ttk.Entry(input_frame, textvariable=self.amount_var, width=15)
        self.amount_entry.grid(row=1, column=1, columnspan=2, padx=5, pady=5)

        # Кнопка
        self.convert_btn = ttk.Button(input_frame, text="Конвертировать", command=self.convert)
        self.convert_btn.grid(row=1, column=3, padx=5)

        # Таблица истории
        self.tree = ttk.Treeview(self.root, columns=("from", "to", "amount", "rate", "result"), show='headings')
        
        self.tree.heading("from", text="Из")
        self.tree.heading("to", text="В")
        self.tree.heading("amount", text="Сумма")
        self.tree.heading("rate", text="Курс")
        self.tree.heading("result", text="Результат")

        self.tree.column("from", width=70)
        self.tree.column("to", width=70)
        self.tree.column("amount", width=80)
        self.tree.column("rate", width=80)
        self.tree.column("result", width=80)
        
        self.tree.pack(fill="both", expand=True, padx=10, pady=5)
        
    def load_currencies(self):
        """Загружает список валют с помощью API"""
        try:
            response = requests.get(f"{API_URL}{API_KEY}/codes")
            data = response.json()
            if data['result'] == 'success':
                # Формируем словарь {код: название}
                self.currencies = {item['currency_code']: f"{item['currency_code']} - {item['currency_name']}" 
                                   for item in data['supported_codes']}
            else:
                messagebox.showerror("Ошибка", f"Не удалось загрузить список валют: {data['error-type']}")
                self.root.destroy()
                
            # Обновляем списки валют в интерфейсе
            if hasattr(self, 'from_currency_combo'):
                values = list(self.currencies.keys())
                self.from_currency_combo['values'] = values
                self.to_currency_combo['values'] = values
                
                if 'USD' in values:
                    self.from_currency_var.set('USD')
                if 'RUB' in values and len(values) > 1:
                    self.to_currency_var.set('RUB')
                    
            return True
            
        except Exception as e:
            messagebox.showerror("Ошибка сети", f"Нет подключения к интернету или ошибка API: {e}")
            self.root.destroy()
            return False

    def convert(self):
        """Логика конвертации"""
        
        # Валидация ввода
        amount_str = self.amount_var.get()
        
        try:
            amount = float(amount_str)
            if amount <= 0:
                raise ValueError("Сумма должна быть положительной.")
                
            from_curr = self.from_currency_var.get()
            to_curr = self.to_currency_var.get()
            
            if from_curr == to_curr:
                raise ValueError("Выберите разные валюты для конвертации.")
                
            if from_curr not in self.currencies or to_curr not in self.currencies:
                raise ValueError("Выбрана несуществующая валюта.")
                
            # Блокируем кнопку на время запроса
            self.convert_btn.state(['disabled'])
            
            # Запрос к API
            response = requests.get(f"{API_URL}{API_KEY}/pair/{from_curr}/{to_curr}/{amount}")
            data = response.json()
            
            if data['result'] == 'success':
                result_amount = data['conversion_result']
                rate = data['conversion_rate']
                
                # Добавляем в историю
                entry = {
                    "from": from_curr,
                    "to": to_curr,
                    "amount": amount,
                    "rate": rate,
                    "result": result_amount,
                    "time": data['time_last_update_utc']
                }
                self.history.append(entry)
                self.save_history()
                
                # Обновляем таблицу
                self.update_history_table()
                
                messagebox.showinfo("Готово!", 
                                    f"{amount} {from_curr} = {result_amount} {to_curr}\nКурс: {rate}")
                
            else:
                messagebox.showerror("Ошибка API", data['error-type'])
                
            self.convert_btn.state(['!disabled'])
            
            
            
            
            
            
            
            
            
            
            
            
            
    def save_history(self):
        """Сохраняет историю в JSON файл"""
        try:
            with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=4)
            print(f"История сохранена в {HISTORY_FILE}")
        except Exception as e:
            print(f"Ошибка при сохранении истории: {e}")

    def load_history(self):
        """Загружает историю из JSON файла"""
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
                    print(f"История загружена из {HISTORY_FILE}")
                    self.update_history_table()
            except Exception as e:
                print(f"Ошибка при загрузке истории: {e}")

    def update_history_table(self):
        """Обновляет данные в таблице Treeview"""
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
    def update_history_table(self):
        """Очищает и заполняет таблицу историей"""
         # Очистка таблицы
         for i in self.tree.get_children():
             self.tree.delete(i)
         
         # Заполнение данными
         for entry in self.history:
             self.tree.insert("", "end", values=(entry["from"], entry["to"], entry["amount"], entry["rate"], entry["result"]))

if __name__ == "__main__":
    root = tk.Tk()
    app = CurrencyConverterApp(root)
    root.mainloop()
