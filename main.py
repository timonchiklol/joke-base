# для проверки на дубликаты настройка
import mysql.connector
import google.generativeai as genai
import os
from dotenv import load_dotenv
from gemini_kolobok import check_joke_duplicate
import sys

class JokeManager:
    def __init__(self):
        # Загрузка переменных окружения
        load_dotenv()
        self.API_KEY = os.getenv("GOOGLE_API_KEY")
        
        # Вывод всех переменных окружения для диагностики
        print("Environment Variables:")
        for key, value in os.environ.items():
            if key.startswith("MYSQL") or key.startswith("DB_"):
                # Маскируем пароли для безопасности в логах
                if "PASS" in key or "PASSWORD" in key:
                    print(f"  {key}: ****")
                else:
                    print(f"  {key}: {value}")
        
        # Используем переменные Railway в приоритете
        self.DB_HOST = os.getenv("MYSQLHOST", os.getenv("DB_HOST", "localhost"))
        self.DB_USER = os.getenv("MYSQLUSER", os.getenv("DB_USER", "root"))
        self.DB_PASS = os.getenv("MYSQLPASSWORD", os.getenv("DB_PASS", ""))
        self.DB_NAME = os.getenv("MYSQLDATABASE", os.getenv("DB_NAME", "jokes_db"))
        self.DB_PORT = os.getenv("MYSQLPORT", os.getenv("DB_PORT", "3306"))
        
        # Отладочная информация
        print(f"Final Database Settings:")
        print(f"  HOST: {self.DB_HOST}")
        print(f"  USER: {self.DB_USER}") 
        print(f"  DATABASE: {self.DB_NAME}")
        print(f"  PORT: {self.DB_PORT}")

# Настройка API
        genai.configure(api_key=self.API_KEY)

# Инициализация модели
        self.model = genai.GenerativeModel('gemini-1.5-flash')

#Категории шуток
        self.categories = ["jokes", "dark_humor", "quotes", "programming", "funniest", "other"]

# Функция для получения и проверки категории
    def get_valid_category(self):
        while True:
            category = input("Enter category: ")
            if category in self.categories:
                return category
            
            print("Error: Invalid category. Available categories:")
            for index, cat in enumerate(self.categories, 1):
                print(f"{index}. {cat}")

# Подключение к базе данных
    def get_db(self):
        try:
            print(f"Connecting to DB: Host={self.DB_HOST}, User={self.DB_USER}, DB={self.DB_NAME}, Port={self.DB_PORT or '3306'}")
            connection = mysql.connector.connect(
                host=self.DB_HOST,
                user=self.DB_USER,
                password=self.DB_PASS,
                database=self.DB_NAME,
                port=int(self.DB_PORT) if self.DB_PORT else 3306
            )
            print("Database connection successful")
            return connection
        except mysql.connector.Error as err:
            print(f"Database connection error: {err}")
            raise

    def initialize_db(self):
        """Создаёт необходимые таблицы, если они не существуют"""
        try:
            print(f"Attempting to initialize database: {self.DB_HOST} (USER: {self.DB_USER}, DB: {self.DB_NAME})")
            conn = mysql.connector.connect(
                host=self.DB_HOST,
                user=self.DB_USER,
                password=self.DB_PASS,
                database=self.DB_NAME,
                port=int(self.DB_PORT) if self.DB_PORT else 3306
            )
            print("Connected to database, creating tables...")
            cursor = conn.cursor()
            
            # Создаём таблицу категорий
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(50) NOT NULL UNIQUE
            )
            """)
            
            # Создаём таблицу шуток
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS jokes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                text TEXT NOT NULL,
                category_id INT,
                FOREIGN KEY (category_id) REFERENCES categories(id)
            )
            """)
            
            # Добавляем стандартные категории
            for category in self.categories:
                try:
                    cursor.execute("""
                    INSERT IGNORE INTO categories (name) VALUES (%s)
                    """, (category,))
                except Exception as e:
                    print(f"Error inserting category {category}: {e}")
            
            conn.commit()
            print("Database initialized successfully")
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"Database initialization failed: {e}")

# Основной цикл программы
class Main:
    def __init__(self):
        self.joke_manager = JokeManager()
        try:
            self.joke_manager.initialize_db()
        except Exception as e:
            print(f"Failed to initialize database: {e}")

    def run(self):
        # Проверяем, работаем ли мы в деплое или локально
        if os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("DEPLOYMENT_ENV") == "production":
            # В Railway запускаем телеграм-бота
            print("Starting Telegram bot...")
            from telegram_bot import main as run_telegram_bot
            run_telegram_bot()
            return
            
        # Остальной код с input() выполняется только при локальном запуске
        while True:
            joke_input = input("Enter a command: ")
            if joke_input == "show":
                category = self.joke_manager.get_valid_category()
        
                # Находим шутку с нужным id
                conn = self.joke_manager.get_db()
                cursor = conn.cursor()
                
                # Получаем ID категории
                cursor.execute("SELECT id FROM categories WHERE name = %s", (category,))
                category_result = cursor.fetchone()
            
                if category_result:
                    category_id = category_result[0]
                    
                    # Получаем все шутки из выбранной категории
                    cursor.execute("SELECT id, text FROM jokes WHERE category_id = %s", (category_id,))
                    jokes = cursor.fetchall()
                    
                    if jokes:
                        print(f"\n=== Jokes from category '{category}' ===")
                        for joke_id, joke_text in jokes:
                            print(f"{joke_id}. {joke_text}")
                    else:
                        print(f"No jokes in category '{category}'.")
                else:
                    print(f"Category '{category}' not found in database.")
            
                cursor.close()
                conn.close()

            elif joke_input == "add":
                joke_input = input("Enter a joke: ")
                category = self.joke_manager.get_valid_category()
                # Проверка на дубликаты
                if check_joke_duplicate(joke_input):
                    # Добавляем в базу данных вместо файла
                    conn = self.joke_manager.get_db()
                    cursor = conn.cursor()
                    
                    # Получаем ID категории (создаем если нет)
                    cursor.execute("SELECT id FROM categories WHERE name = %s", (category,))
                    result = cursor.fetchone()
                    if result:
                        category_id = result[0]
                    else:
                        cursor.execute("INSERT INTO categories (name) VALUES (%s)", (category,))
                        conn.commit()
                        category_id = cursor.lastrowid
                    
                    # Добавляем шутку
                    cursor.execute("INSERT INTO jokes (text, category_id) VALUES (%s, %s)", 
                                (joke_input, category_id))
                    conn.commit()
                    cursor.close()
                    conn.close()
                    print("Joke added to database.")
                else:
                    print("Joke rejected. Similar joke already exists.")


            elif joke_input == "change":
                category = self.joke_manager.get_valid_category()
                
                conn = self.joke_manager.get_db()
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT j.id, j.text FROM jokes j 
                    JOIN categories c ON j.category_id = c.id 
                    WHERE c.name = %s
                """, (category,))
                
                jokes = cursor.fetchall()
                
                if not jokes:
                    print(f"No jokes in category '{category}'.")
                    cursor.close()
                    conn.close()
                    continue
                
                for joke_id, joke_text in jokes:
                    print(f"{joke_id}: {joke_text}")
                
                try:
                    joke_number = int(input("Enter joke number: "))
                    new_joke = input("Enter new joke: ")
                    
                    cursor.execute("""
                        UPDATE jokes SET text = %s 
                        WHERE id = %s AND category_id = (
                            SELECT id FROM categories WHERE name = %s
                        )
                    """, (new_joke, joke_number, category))
                    conn.commit()
                    
                    if cursor.rowcount > 0:
                        print("Joke updated.")
                    else:
                        print("Error: Joke not found.")
                        
                    cursor.close()
                    conn.close()
                except ValueError:
                    print("Error: Enter valid number.")
                    cursor.close()
                    conn.close()


            elif joke_input == "delete":
                # Берем шутки из базы данных вместо файла
                conn = self.joke_manager.get_db()
                cursor = conn.cursor()
                
                try:
                    joke_number = int(input("Enter a joke number: "))
                    category = self.joke_manager.get_valid_category()
                    
                    # Удаляем шутку из базы данных
                    cursor.execute("""
                        DELETE FROM jokes 
                        WHERE id = %s AND category_id = (
                            SELECT id FROM categories WHERE name = %s
                        )
                    """, (joke_number, category))
                    conn.commit()
                    if cursor.rowcount > 0:
                        print("Joke deleted.")
                    else:
                        print("Error: Joke with this number doesn't exist.")
                        
                    cursor.close()
                    conn.close()
                except ValueError:
                    print("Error: Enter a valid joke number (integer).")
                            
            elif joke_input == "clear":
                conn = self.joke_manager.get_db()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM jokes")
                conn.commit()
                cursor.close()
                conn.close()
                print("Database cleared.")

# Добавьте эти строки в самый конец файла
if __name__ == "__main__":
    app = Main()
    app.run()
