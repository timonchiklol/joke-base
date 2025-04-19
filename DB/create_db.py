import mysql.connector
import os
# Замените на свой пароль MySQL
DB_PASS = os.getenv("DB_PASS") 

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
    
    print("✅ База данных jokes_db успешно создана!")
    conn.close()
    
except Exception as e:
    print(f"❌ Ошибка: {e}") 