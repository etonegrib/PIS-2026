import tkinter as tk
from tkinter import ttk, messagebox
from database import CinemaDB


class CinemaUI:
    def __init__(self, root):
        self.db = CinemaDB()
        self.root = root
        self.root.title("CinemaBY — Кассовый терминал")
        self.root.geometry("600x650")
        self.root.configure(bg="#1e1e2e")  # Темный современный фон

        self.apply_styles()
        self.create_widgets()

    def apply_styles(self):
        style = ttk.Style()
        style.theme_use('clam')  # Используем 'clam' как базу для кастомизации

        # Настройка цветов
        bg_color = "#1e1e2e"
        card_color = "#2b2b3b"
        accent_color = "#00c896"  # Приятный мятный цвет
        text_color = "#ffffff"

        # Стиль для контейнеров
        style.configure("TFrame", background=bg_color)
        style.configure("Card.TFrame", background=card_color, relief="flat")

        # Стиль для надписей
        style.configure("TLabel",
                        background=bg_color,
                        foreground=text_color,
                        font=("Segoe UI", 10))

        style.configure("Header.TLabel",
                        font=("Segoe UI Semibold", 16),
                        foreground=accent_color)

        # Стиль для кнопок
        style.configure("Action.TButton",
                        font=("Segoe UI Bold", 10),
                        background=accent_color,
                        foreground="white",
                        borderwidth=0)
        style.map("Action.TButton",
                  background=[('active', '#00a67d')])

        style.configure("Secondary.TButton",
                        font=("Segoe UI", 10),
                        background="#44445a",
                        foreground="white")

        # Настройка полей ввода и комбобоксов
        style.configure("TCombobox", fieldbackground="#3b3b4f", background="#3b3b4f", foreground="white")
        style.configure("TEntry", fieldbackground="#3b3b4f", foreground="white")

    def create_widgets(self):
        # Главный контейнер с отступами
        main_frame = ttk.Frame(self.root, padding="30")
        main_frame.pack(fill="both", expand=True)

        # Заголовок
        header = ttk.Label(main_frame, text="ОФОРМЛЕНИЕ БИЛЕТА", style="Header.TLabel")
        header.pack(pady=(0, 25))

        # Карточка формы
        form_card = ttk.Frame(main_frame, style="Card.TFrame", padding="20")
        form_card.pack(fill="x", pady=5)

        # Поле: Фамилия
        ttk.Label(form_card, text="Фамилия клиента", background="#2b2b3b").pack(anchor="w")
        self.ent_name = tk.Entry(form_card, bg="#3b3b4f", fg="white", insertbackground="white",
                                 relief="flat", font=("Segoe UI", 11), bd=8)
        self.ent_name.pack(fill="x", pady=(5, 15))

        # Поле: Выбор сеанса
        ttk.Label(form_card, text="Выберите сеанс и зал", background="#2b2b3b").pack(anchor="w")
        self.combo_session = ttk.Combobox(form_card, state="readonly", font=("Segoe UI", 10))
        self.combo_session.pack(fill="x", pady=(5, 15))

        # Поле: Количество
        ttk.Label(form_card, text="Количество мест (BYN)", background="#2b2b3b").pack(anchor="w")
        self.ent_qty = tk.Entry(form_card, bg="#3b3b4f", fg="white", insertbackground="white",
                                relief="flat", font=("Segoe UI", 11), bd=8)
        self.ent_qty.insert(0, "1")
        self.ent_qty.pack(fill="x", pady=(5, 10))

        # Кнопки
        btn_buy = ttk.Button(main_frame, text="ПОДТВЕРДИТЬ ПОКУПКУ",
                             style="Action.TButton", command=self.process_buy)
        btn_buy.pack(pady=(25, 10), fill="x", ipady=10)

        btn_report = ttk.Button(main_frame, text="ПРОСМОТРЕТЬ ЖУРНАЛ ПРОДАЖ",
                                style="Secondary.TButton", command=self.show_report)
        btn_report.pack(fill="x", ipady=5)

        # Футер
        ttk.Label(main_frame, text="CinemaBY v2.0 | Transaction Script Lab",
                  font=("Segoe UI", 8), foreground="#666680").pack(side="bottom", pady=10)

        self.load_sessions()

    def load_sessions(self):
        data = self.db.get_movies_and_halls()
        self.session_map = {}
        values = []
        for m_id, m_title, h_id, h_name, seats, price in data:
            label = f"{m_title.upper()} — {h_name} — {price} BYN"
            values.append(label)
            self.session_map[label] = (m_id, h_id)
        self.combo_session['values'] = values
        if values: self.combo_session.current(0)

    def process_buy(self):
        name = self.ent_name.get().strip()
        session_label = self.combo_session.get()
        qty_str = self.ent_qty.get()

        if not name or not qty_str:
            messagebox.showwarning("Внимание", "Пожалуйста, заполните все данные")
            return

        try:
            qty = int(qty_str)
            m_id, h_id = self.session_map[session_label]
            success, message = self.db.buy_ticket_transaction(m_id, h_id, name, qty)

            if success:
                messagebox.showinfo("Готово", message)
                self.load_sessions()
                self.ent_name.delete(0, tk.END)
            else:
                messagebox.showerror("Ошибка транзакции", message)
        except ValueError:
            messagebox.showerror("Ошибка", "Введите число в поле количества")

    def show_report(self):
        report_win = tk.Toplevel(self.root)
        report_win.title("Журнал транзакций")
        report_win.geometry("800x400")
        report_win.configure(bg="#1e1e2e")

        # Стилизация таблицы (Treeview)
        style = ttk.Style()
        style.configure("Treeview", background="#2b2b3b", foreground="white",
                        fieldbackground="#2b2b3b", rowheight=30)
        style.map("Treeview", background=[('selected', '#00c896')])

        cols = ("ID", "Клиент", "Фильм", "Зал", "Места", "Итого (BYN)")
        tree = ttk.Treeview(report_win, columns=cols, show="headings", selectmode="browse")

        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, anchor="center")

        tickets = self.db.get_all_tickets()
        for t in tickets:
            tree.insert("", "end", values=t)

        tree.pack(fill="both", expand=True, padx=20, pady=20)


if __name__ == "__main__":
    root = tk.Tk()
    app = CinemaUI(root)
    root.mainloop()