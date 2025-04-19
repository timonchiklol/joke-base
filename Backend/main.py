# для проверки на дубликаты настройка
import mysql.connector
import google.generativeai as genai
import os
from dotenv import load_dotenv
from gemini_kolobok import check_joke_duplicate
# Загрузка переменных окружения
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")  
DB_NAME = os.getenv("DB_NAME")

# Настройка API
genai.configure(api_key=API_KEY)

# Инициализация модели
model = genai.GenerativeModel('gemini-1.5-flash')

#Категории шуток
categories = ["jokes", "dark_humor", "quotes", "programming", "funniest", "other"]

# Проверка на категорию
#def check_category(category):
#    if category not in categories:
#        print("Ошибка: Неверная категория. Доступные категории:")
#        for index, category in enumerate(categories, 1):
#            print(f"{index}. {category}")
#        return False
#    return True

# Подключение к базе данных
def get_db():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME
    )

while True:
    joke_input = input("Enter a command: ")
    if joke_input == "show":
        # Берем шутки из базы данных
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, text FROM jokes")
        jokes = cursor.fetchall()
        cursor.close()
        conn.close()
        
        category = input("Enter category: ")
        if category not in categories:
            print("Ошибка: Неверная категория. Доступные категории:")
            for index, category in enumerate(categories, 1):
                print(f"{index}. {category}")
            continue
        # Находим шутку с нужным id
        conn = get_db()
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
                print(f"\n=== Шутки из категории '{category}' ===")
                for joke_id, joke_text in jokes:
                    print(f"{joke_id}. {joke_text}")
            else:
                print(f"В категории '{category}' нет шуток.")
        else:
            print(f"Категория '{category}' не найдена в базе данных.")
        
        cursor.close()
        conn.close()


    elif joke_input == "add":
        joke_input = input("Enter a joke: ")
        category = input("Enter category: ")
        if category not in categories:
            print("Ошибка: Неверная категория. Доступные категории:")
            for index, category in enumerate(categories, 1):
                print(f"{index}. {category}")
            continue
        # Проверка на дубликаты
        if check_joke_duplicate(joke_input):
            # Добавляем в базу данных вместо файла
            conn = get_db()
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
            print("Шутка добавлена в базу данных.")
        else:
            print("Шутка отклонена. Похожая шутка уже существует.")


    elif joke_input == "change":
        category = input("Enter category: ")
        if category not in categories:
            print("Error: Invalid category. Available categories:")
            for index, category in enumerate(categories, 1):
                print(f"{index}. {category}")
            continue
        
        conn = get_db()
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
        conn = get_db()
        cursor = conn.cursor()
        
        try:
            joke_number = int(input("Enter a joke number: "))
            category = input("Enter category: ")
            # Удаляем шутку из базы данных
            cursor.execute("""
                DELETE FROM jokes 
                WHERE id = %s AND category_id = (
                    SELECT id FROM categories WHERE name = %s
                )
            """, (joke_number, category))
            conn.commit()
            if category not in categories:
                print("Ошибка: Неверная категория. Доступные категории:")
                for index, category in enumerate(categories, 1):
                    print(f"{index}. {category}")
                continue
            if cursor.rowcount > 0:
                print("Шутка удалена.")
            else:
                print("Ошибка: Шутка с таким номером не существует.")
                
            cursor.close()
            conn.close()
        except ValueError:
            print("Ошибка: Введите корректный номер шутки (целое число).")
                    
    elif joke_input == "clear":
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM jokes")
        conn.commit()
        cursor.close()
        conn.close()
        print("База данных очищена.")
