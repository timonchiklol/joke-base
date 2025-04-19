import mysql.connector
import os
from dotenv import load_dotenv

# Загрузка переменных из .env файла
load_dotenv()
DB_PASS = os.getenv("DB_PASS")

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password=DB_PASS,
        database="jokes_db"
    )

def view_database():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print("\n=== КАТЕГОРИИ ===")
    cursor.execute("SELECT id, name FROM categories")
    categories = cursor.fetchall()
    
    if not categories:
        print("Нет категорий в базе данных.")
    else:
        for cat_id, cat_name in categories:
            print(f"{cat_id}: {cat_name}")
    
    print("\n=== ШУТКИ ===")
    cursor.execute("""
    SELECT j.id, j.text, c.name 
    FROM jokes j 
    LEFT JOIN categories c ON j.category_id = c.id
    """)
    
    jokes = cursor.fetchall()
    
    if not jokes:
        print("Нет шуток в базе данных.")
    else:
        for joke_id, joke_text, category in jokes:
            print(f"{joke_id}. [{category}] {joke_text}")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    view_database() 