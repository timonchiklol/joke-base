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
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME
    )

def check_joke_duplicate(new_joke):
    """Checks if the joke is a duplicate using the database"""
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, text FROM jokes")
    all_jokes = cursor.fetchall()
    cursor.close()
    conn.close()
    
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
    try:
        response = model.generate_content(prompt)
        result = response.text.strip().lower()
        
        # Ищем фразы о схожести
        import re
        similarity_match = re.search(r'similar to joke number (\d+) with similarity score (0\.\d+|1\.0)', result)
        
        if similarity_match:
            joke_number = int(similarity_match.group(1))
            similarity_score = float(similarity_match.group(2))
            
            # Если оценка сходства выше порога
            if similarity_score > 0.7 and 0 < joke_number <= len(existing_jokes):
                similar_joke = existing_jokes[joke_number-1]
                return True, similar_joke, similarity_score
        
        # Если не нашли совпадений или низкая оценка
        return False, None, 0.0
    except Exception as e:
        print(f"Error in check_joke_duplicate: {e}")
        return False, None, 0.0
