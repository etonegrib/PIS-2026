import sqlite3

def setup():
    conn = sqlite3.connect("cinema.db")
    cursor = conn.cursor()

    cursor.executescript('''
        CREATE TABLE IF NOT EXISTS movies (id INTEGER PRIMARY KEY, title TEXT, base_price REAL);
        CREATE TABLE IF NOT EXISTS halls (id INTEGER PRIMARY KEY, name TEXT, price_modifier REAL);
        CREATE TABLE IF NOT EXISTS movie_halls (
            movie_id INTEGER, hall_id INTEGER, available_seats INTEGER,
            PRIMARY KEY (movie_id, hall_id)
        );
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT, customer_name TEXT,
            movie_id INTEGER, hall_id INTEGER, quantity INTEGER, total_sum REAL
        );
    ''')

    # Наполнение
    movies = [('Дюна', 12.0), ('Бэтмен', 10.5), ('Аватар', 15.0), ('Оппенгеймер', 13.0)]
    cursor.executemany("INSERT OR IGNORE INTO movies (title, base_price) VALUES (?, ?)", movies)

    halls = [('Большой зал', 1.0), ('Малый зал (VIP)', 1.5)]
    cursor.executemany("INSERT OR IGNORE INTO halls (name, price_modifier) VALUES (?, ?)", halls)

    # Привязка фильмов к залам
    sessions = [(1,1,100), (1,2,20), (2,1,80), (3,1,120), (4,2,25)]
    cursor.executemany("INSERT OR IGNORE INTO movie_halls VALUES (?, ?, ?)", sessions)

    conn.commit()
    conn.close()
    print("База данных инициализирована.")

if __name__ == "__main__":
    setup()