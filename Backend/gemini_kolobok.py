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
    """Проверяет шутку на дубликат, используя базу данных"""
    
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
    Проверь, похожа ли новая шутка на какую-либо из существующих шуток.
    
    Существующие шутки:
    {jokes_text}
    
    Новая шутка: {new_joke}
    
    Если новая шутка похожа на какую-то из существующих (смысл тот же), 
    ответь:"false" и в ином случае ответь:"true"
    """
    
    # Отправляем запрос к модели
    response = model.generate_content(prompt)
    result = response.text.strip()
    
    # Проверяем результат
    if "false" in result:
        return False
    elif "true" in result:
        return True
    else:
        return "нихера не работает"
