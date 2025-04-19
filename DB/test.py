import mysql.connector

try:
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="DB_PASS"
    )
    print("Подключение успешно!")
    conn.close()
except Exception as e:
    print(f"Ошибка: {e}")
