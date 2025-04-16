# для проверки на дубликаты настройка
from gemini_kolobok import check_joke_duplicate
import google.generativeai as genai
import os
from dotenv import load_dotenv
load_dotenv()
# Настройка API
API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=API_KEY)

# Инициализация модели
model = genai.GenerativeModel('gemini-1.5-flash')

#категории шуток
categories = []


while True:
    joke_input = input("Enter a command: ")
    if joke_input == "show":
        with open("jokes.txt", "r") as file:
            jokes = file.readlines()
            try:
                joke_number = int(input("Enter a joke number: "))
                print(jokes[joke_number])
            except IndexError:
                print("Ошибка: Шутка с таким номером не существует.")
            except ValueError:
                print("Ошибка: Введите корректный номер шутки (целое число).")


    elif joke_input == "add":
        joke_input = input("Enter a joke: ")
        if check_joke_duplicate(joke_input):
            with open("jokes.txt", "a", encoding="utf-8") as file:
                file.write(joke_input + "\n")
                print("Шутка добавлена в базу данных.")
        else:
            print("Шутка отклонена. Похожая шутка уже существует.")


    elif joke_input == "change":
        with open("jokes.txt", "r") as file:
            jokes = file.readlines()
            try:
                joke_number = int(input("Enter a joke number: "))
                new_joke = input("Enter a new joke: ")
                jokes[joke_number] = new_joke + "\n"
                with open("jokes.txt", "w") as file:
                    file.writelines(jokes)
                print("Шутка изменена.")
            except IndexError:
                print("Ошибка: Шутка с таким номером не существует.")
            except ValueError:
                print("Ошибка: Введите корректный номер шутки (целое число).")


    elif joke_input == "delete":
        with open("jokes.txt", "r") as file:
            jokes = file.readlines()
            try:
                joke_number = int(input("Enter a joke number: "))
                del jokes[joke_number+1]
                with open("jokes.txt", "w") as file:
                    file.writelines(jokes)
                print("Шутка удалена.")
            except IndexError:
                print("Ошибка: Шутка с таким номером не существует.")
            except ValueError:
                print("Ошибка: Введите корректный номер шутки (целое число).")
                    
