import mysql.connector

try:
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="DB_PASS"
    )
    print("CONNECTION SUCCESS!")
    conn.close()
except Exception as e:
    print(f"ERROR: {e}")
