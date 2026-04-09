import sqlite3
import json


class CinemaDB:
    def __init__(self, db_name="cinema.db", json_name="backup.json"):
        self.db_name = db_name
        self.json_name = json_name

    def _get_connection(self):
        return sqlite3.connect(self.db_name)

    def buy_ticket_transaction(self, movie_id, hall_id, customer_name, qty):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("BEGIN TRANSACTION")

            # 1. Проверка наличия мест в конкретном зале для конкретного фильма
            cursor.execute("""
                SELECT available_seats, price_modifier 
                FROM movie_halls 
                JOIN halls ON movie_halls.hall_id = halls.id
                WHERE movie_id = ? AND hall_id = ?
            """, (movie_id, hall_id))

            result = cursor.fetchone()
            if not result:
                raise Exception("Сеанс в данном зале не найден")

            seats_left, modifier = result
            if seats_left < qty:
                raise Exception(f"Мест нет. Осталось: {seats_left}")

            # 2. Расчет стоимости (Базовая цена фильма * модификатор зала)
            cursor.execute("SELECT title, base_price FROM movies WHERE id = ?", (movie_id,))
            movie_title, base_price = cursor.fetchone()
            total_price = round(base_price * modifier * qty, 2)

            # 3. Обновление остатка мест
            cursor.execute("""
                UPDATE movie_halls SET available_seats = available_seats - ? 
                WHERE movie_id = ? AND hall_id = ?
            """, (qty, movie_id, hall_id))

            # 4. Регистрация билета
            cursor.execute("""
                INSERT INTO tickets (customer_name, movie_id, hall_id, quantity, total_sum)
                VALUES (?, ?, ?, ?, ?)
            """, (customer_name, movie_id, hall_id, qty, total_price))

            conn.commit()
            self.export_to_json()  # Синхронизация с JSON после успеха
            return True, f"Успешно! Сумма: {total_price} BYN"

        except Exception as e:
            conn.rollback()
            return False, str(e)
        finally:
            conn.close()

    def export_to_json(self):
        conn = self._get_connection()
        cursor = conn.cursor()

        # Собираем все данные для бэкапа
        cursor.execute("SELECT * FROM movies")
        movies = cursor.fetchall()
        cursor.execute("SELECT * FROM tickets")
        tickets = cursor.fetchall()

        data = {"movies": movies, "tickets": tickets}
        with open(self.json_name, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        conn.close()

    def get_movies_and_halls(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT m.id, m.title, h.id, h.name, mh.available_seats, m.base_price * h.price_modifier
            FROM movie_halls mh
            JOIN movies m ON mh.movie_id = m.id
            JOIN halls h ON mh.hall_id = h.id
            WHERE mh.available_seats > 0
        """)
        data = cursor.fetchall()
        conn.close()
        return data

    def get_all_tickets(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT t.id, t.customer_name, m.title, h.name, t.quantity, t.total_sum 
            FROM tickets t
            JOIN movies m ON t.movie_id = m.id
            JOIN halls h ON t.hall_id = h.id
        """)
        data = cursor.fetchall()
        conn.close()
        return data