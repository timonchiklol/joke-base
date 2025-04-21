import mysql.connector
import os
from dotenv import load_dotenv
import google.generativeai as genai
import os
from dotenv import load_dotenv
load_dotenv()
# Настройка API
API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=API_KEY)

# Инициализация модели
model = genai.GenerativeModel('gemini-1.5-flash')

# Загрузка переменных окружения
load_dotenv()
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_NAME = os.getenv("DB_NAME")
    
# Подключение к базе данных
def get_db():
    """Улучшенная функция подключения к базе данных"""
    # Используем переменные Railway в приоритете (как в main.py)
    DB_HOST = os.getenv("MYSQLHOST", os.getenv("DB_HOST", "localhost"))
    DB_USER = os.getenv("MYSQLUSER", os.getenv("DB_USER", "root"))
    DB_PASS = os.getenv("MYSQLPASSWORD", os.getenv("DB_PASS", ""))
    DB_NAME = os.getenv("MYSQLDATABASE", os.getenv("DB_NAME", "jokes_db"))
    DB_PORT = os.getenv("MYSQLPORT", os.getenv("DB_PORT", "3306"))
    
    print(f"Attempting to connect to DB: {DB_HOST}:{DB_PORT}/{DB_NAME}")
    
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
        port=DB_PORT
    )

def check_joke_duplicate(new_joke):
    """Checks if the joke is a duplicate using the database"""
    try:
        print("Starting duplicate check for joke:", new_joke[:20] + "...")
        
        # Детальное логирование подключения к БД
        print("Attempting to connect to database")
        conn = get_db()
        print("Successfully connected to database")
        cursor = conn.cursor()
        cursor.execute("SELECT id, text FROM jokes")
        all_jokes = cursor.fetchall()
        print(f"Retrieved {len(all_jokes)} jokes from database")
        cursor.close()
        conn.close()
        
        # Если нет шуток, не может быть дубликатов
        if not all_jokes:
            print("No jokes in database, skipping duplicate check")
            return False, None, 0.0
        
        # Преобразуем список шуток из базы данных в список текстов шуток
        existing_jokes = [joke[1] for joke in all_jokes]
        
        # Формируем запрос со всеми шутками сразу
        jokes_text = "\n".join([f"{i+1}. {joke}" for i, joke in enumerate(existing_jokes)])
        
        prompt = f"""
        Check if the new joke is similar to any of the existing jokes.
        
        Existing jokes:
        {jokes_text}
        
        New joke: {new_joke}
        
        Analyze and respond in this format:
        1. Similar to joke number X with similarity score Y (0.0-1.0)
        2. OR respond "No similar jokes found"
        
        If similarity score > 0.7, the joke is considered a duplicate.
        """
        
        # Отправляем запрос к модели
        print("Sending request to Gemini model...")
        response = model.generate_content(prompt)
        result = response.text.strip().lower()
        print(f"Gemini response: {result}")
        
        # Ищем фразы о схожести
        import re
        similarity_match = re.search(r'similar to joke number (\d+) with similarity score (0\.\d+|1\.0)', result)
        
        if similarity_match:
            joke_number = int(similarity_match.group(1))
            similarity_score = float(similarity_match.group(2))
            print(f"Found similarity: joke #{joke_number} with score {similarity_score}")
            
            # Если оценка сходства выше порога
            if similarity_score > 0.7 and 0 < joke_number <= len(existing_jokes):
                similar_joke = existing_jokes[joke_number-1]
                print(f"Joke IS a duplicate with score {similarity_score}")
                return True, similar_joke, similarity_score
        
        print("Joke is NOT a duplicate")
        # Если не нашли совпадений или низкая оценка
        return False, None, 0.0
    
    except mysql.connector.errors.DatabaseError as e:
        print(f"*** DATABASE ERROR in check_joke_duplicate: {e}")
        print(f"Connection parameters:")
        print(f"  HOST: {os.getenv('MYSQLHOST', os.getenv('DB_HOST', 'localhost'))}")
        print(f"  USER: {os.getenv('MYSQLUSER', os.getenv('DB_USER', 'root'))}")
        print(f"  DB  : {os.getenv('MYSQLDATABASE', os.getenv('DB_NAME', 'jokes_db'))}")
        print(f"  PORT: {os.getenv('MYSQLPORT', os.getenv('DB_PORT', '3306'))}")
        # Пропускаем проверку на дубликаты при ошибке подключения
        return False, None, 0.0
    
    except Exception as e:
        print(f"*** GENERAL ERROR in check_joke_duplicate: {e}")
        import traceback
        traceback.print_exc()
        return False, None, 0.0
