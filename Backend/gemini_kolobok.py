import google.generativeai as genai
import os
from dotenv import load_dotenv
load_dotenv()
# Настройка API
API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=API_KEY)

# Инициализация модели
model = genai.GenerativeModel('gemini-1.5-flash')

def check_joke_duplicate(new_joke, jokes_file="jokes.txt"):
    """Проверяет шутку на дубликат, передавая весь файл в один запрос"""
    
    # Читаем существующие шутки
    existing_jokes = []
    with open(jokes_file, "r", encoding="utf-8") as file:
        existing_jokes = [line.strip() for line in file.readlines()]
    
    # Формируем запрос со всеми шутками сразу
    jokes_text = "\n".join([f"{i+1}. {joke}" for i, joke in enumerate(existing_jokes)])
    # надо разобратся с этой строчкой которая выше
    
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
