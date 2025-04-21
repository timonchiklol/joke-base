import mysql.connector
import os
from dotenv import load_dotenv

# Загрузка переменных из .env файла
load_dotenv()
# Замените на свой пароль MySQL
DB_PASS = os.getenv("DB_PASS") 

# Предопределенные категории
categories = {
    "jokes": "",
    "dark_humor": "",
    "quotes": "",
    "programming": "",
    "funniest": "",
    "other": ""
}

try:
    # Подключение к MySQL
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password=DB_PASS
    )
    cursor = conn.cursor()
    
    # Создание базы данных
    cursor.execute("CREATE DATABASE IF NOT EXISTS jokes_db")
    cursor.execute("USE jokes_db")
    
    # Создание таблицы категорий
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS categories (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255) UNIQUE NOT NULL,
        description TEXT
    )
    """)
    
    # Создание таблицы шуток
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS jokes (
        id INT AUTO_INCREMENT PRIMARY KEY,
        text TEXT NOT NULL,
        category_id INT,
        FOREIGN KEY (category_id) REFERENCES categories(id)
    )
    """)
    
    # Добавление предопределенных категорий
    for category_name, description in categories.items():
        try:
            cursor.execute(
                "INSERT INTO categories (name, description) VALUES (%s, %s)", 
                (category_name, description)
            )
        except mysql.connector.IntegrityError:
            # Категория уже существует, пропускаем
            pass
    
    conn.commit()
    
    # Удаление категории "pol" и "politics"
    cursor.execute("DELETE FROM categories WHERE name IN ('pol', 'politics')")
    conn.commit()
    
    print("✅ DATA BASE SETUP with predefined categories:")
    
    # Выводим список категорий
    cursor.execute("SELECT id, name FROM categories")
    for cat_id, cat_name in cursor.fetchall():
        print(f"   - {cat_id}: {cat_name}")
    
    conn.close()
    
except Exception as e:
    print(f"❌ ERROR: {e}") 