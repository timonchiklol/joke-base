import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters, ConversationHandler
from dotenv import load_dotenv
import os
from gemini_kolobok import check_joke_duplicate
from main import JokeManager

# Загрузка переменных окружения
load_dotenv()
TG_TOKEN = os.getenv("TG_TOKEN")  # Убедитесь, что имя переменной правильное
ADMIN_ID = os.getenv("ADMIN_ID")  # Добавьте свой ID в .env файл

# Константы для состояний разговора
CATEGORY, JOKE_TEXT, JOKE_ID, NEW_JOKE = range(4)

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация менеджера шуток
joke_manager = JokeManager()

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hello! I'm a joke management bot. Use the following commands:\n"
        "/show - show jokes\n"
        "/add - add a joke\n"
        "/change - change a joke\n"
        "/delete - delete a joke\n"
        "/clear - clear the database"
    )

# Обработчик команды /show
async def show(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []
    for category in joke_manager.categories:
        keyboard.append([InlineKeyboardButton(category, callback_data=f"show_{category}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Select a category:", reply_markup=reply_markup)

# Обработчик выбора категории для показа шуток
async def show_category_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    category = query.data.split("_")[1]
    
    conn = joke_manager.get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM categories WHERE name = %s", (category,))
    category_result = cursor.fetchone()
    
    if category_result:
        category_id = category_result[0]
        
        cursor.execute("SELECT id, text FROM jokes WHERE category_id = %s", (category_id,))
        jokes = cursor.fetchall()
        
        if jokes:
            message = f"Jokes from category '{category}':\n\n"
            for joke_id, joke_text in jokes:
                message += f"{joke_id}. {joke_text}\n\n"
            await query.edit_message_text(message)
        else:
            await query.edit_message_text(f"No jokes in category '{category}'.")
    else:
        await query.edit_message_text(f"Category '{category}' not found in database.")
    
    cursor.close()
    conn.close()

# Обработчик команды /add
async def add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []
    for category in joke_manager.categories:
        keyboard.append([InlineKeyboardButton(category, callback_data=f"add_{category}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Select a category for new joke:", reply_markup=reply_markup)
    return JOKE_TEXT

# Обработчик выбора категории для добавления
async def add_category_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    category = query.data.split("_")[1]
    context.user_data['category'] = category
    
    await query.edit_message_text(f"Selected category: {category}\nEnter joke text:")
    return JOKE_TEXT

# Функция для установки меню команд - убираем clear из публичного меню
async def setup_commands(application):
    commands = [
        ("start", "Start the bot"),
        ("show", "Show jokes"),
        ("add", "Add a joke"),
        ("change", "Change a joke"),
        ("delete", "Delete a joke")
        # clear удален из списка видимых команд
    ]
    
    await application.bot.set_my_commands(commands)
    logger.info("Bot commands have been set")

# Общая функция для отправки запроса на модерацию
async def send_for_moderation(context, user_id, command_type, payload, message=None):
    # Сохраняем данные в контексте
    context.bot_data['pending_action'] = {
        'command': command_type,
        'payload': payload,
        'user_id': user_id
    }
    
    # Создаем клавиатуру с кнопками
    keyboard = [
        [
            InlineKeyboardButton("Approve", callback_data=f"approve_{user_id}"),
            InlineKeyboardButton("Decline", callback_data=f"decline_{user_id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
            # Формируем текст для модерации
    mod_text = f"Action request:\nCommand: {command_type}\n"
    if command_type == "add":
        mod_text += f"Category: {payload['category']}\nJoke: {payload['joke_text']}"
    elif command_type == "delete":
        mod_text += f"Joke ID: {payload['joke_id']}\nCategory: {payload['category']}"
    elif command_type == "change":
        mod_text += f"Joke ID: {payload['joke_id']}\nNew text: {payload['new_text']}"
    elif command_type == "clear":
        mod_text += "Request to clear the entire database!"
    
    mod_text += f"\nFrom user: {user_id}"
    
    # Отправляем администратору на проверку
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=mod_text,
        reply_markup=reply_markup
    )
    
    # Сообщаем пользователю
    if message:
        await message.reply_text("Your request has been sent for moderation.")

# Обработчик ввода текста шутки - обновленный с использованием общей функции модерации
async def add_joke_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    joke_text = update.message.text
    category = context.user_data.get('category')
    user_id = update.effective_user.id
    
    # Всегда отправляем на модерацию, без проверки на дубликаты
    await send_for_moderation(
        context=context,
        user_id=user_id,
        command_type="add",
        payload={'category': category, 'joke_text': joke_text},
        message=update.message
    )
    
    return ConversationHandler.END

# Добавляем команду для удаления шутки
async def delete_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Enter joke ID to delete:")
    return JOKE_ID

async def delete_joke_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        joke_id = int(update.message.text)
        context.user_data['joke_id'] = joke_id
        
        # Показываем категории
        keyboard = []
        for category in joke_manager.categories:
            keyboard.append([InlineKeyboardButton(category, callback_data=f"delete_{category}")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Select joke category:", reply_markup=reply_markup)
        return CATEGORY
    except ValueError:
        await update.message.reply_text("Please enter a valid number.")
        return JOKE_ID

async def delete_category_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    category = query.data.split("_")[1]
    joke_id = context.user_data.get('joke_id')
    user_id = update.effective_user.id
    
    # Отправляем на модерацию
    await send_for_moderation(
        context=context,
        user_id=user_id,
        command_type="delete",
        payload={'category': category, 'joke_id': joke_id},
        message=query
    )
    
    await query.edit_message_text(f"Request to delete joke #{joke_id} has been sent for moderation.")
    return ConversationHandler.END

# Команда clear (скрытая, но доступная)
async def clear_database(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # Отправляем на модерацию
    await send_for_moderation(
        context=context,
        user_id=user_id,
        command_type="clear",
        payload={},
        message=update.message
    )
    
    return ConversationHandler.END

# Обновленный обработчик модерации
async def process_admin_decision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # Получаем действие и ID пользователя
    action, user_id = query.data.split("_")
    user_id = int(user_id)  # Преобразуем в число
    
    # Получаем данные запроса из контекста
    pending_action = context.bot_data.get('pending_action', {})
    command = pending_action.get('command')
    payload = pending_action.get('payload', {})
    
    if action == "approve":
        # Обрабатываем в зависимости от типа команды
        if command == "add":
            joke_text = payload.get('joke_text')
            category = payload.get('category')
            
            # Добавляем шутку в базу данных
            conn = joke_manager.get_db()
            cursor = conn.cursor()
            
            cursor.execute("SELECT id FROM categories WHERE name = %s", (category,))
            result = cursor.fetchone()
            if result:
                category_id = result[0]
            else:
                cursor.execute("INSERT INTO categories (name) VALUES (%s)", (category,))
                conn.commit()
                category_id = cursor.lastrowid
            
            cursor.execute("INSERT INTO jokes (text, category_id) VALUES (%s, %s)", 
                        (joke_text, category_id))
            conn.commit()
            cursor.close()
            conn.close()
            
            # Уведомляем администратора и пользователя
            await query.edit_message_text(f"Joke approved and added to the database:\n{joke_text}")
            await context.bot.send_message(chat_id=user_id, text="Your joke has been approved and added!")
            
        elif command == "delete":
            joke_id = payload.get('joke_id')
            category = payload.get('category')
            
            # Удаляем шутку из базы данных
            conn = joke_manager.get_db()
            cursor = conn.cursor()
            
            cursor.execute("""
                DELETE FROM jokes 
                WHERE id = %s AND category_id = (
                    SELECT id FROM categories WHERE name = %s
                )
            """, (joke_id, category))
            conn.commit()
            
            if cursor.rowcount > 0:
                await query.edit_message_text(f"Joke #{joke_id} has been deleted.")
                await context.bot.send_message(chat_id=user_id, text=f"Your request to delete joke #{joke_id} has been approved.")
            else:
                await query.edit_message_text(f"Error: Joke #{joke_id} not found in category {category}.")
                await context.bot.send_message(chat_id=user_id, text=f"Error: Joke #{joke_id} not found in category {category}.")
                
            cursor.close()
            conn.close()
            
        elif command == "change":
            joke_id = payload.get('joke_id')
            new_text = payload.get('new_text')
            
            # Изменяем текст шутки в базе данных
            conn = joke_manager.get_db()
            cursor = conn.cursor()
            
            cursor.execute("UPDATE jokes SET text = %s WHERE id = %s", (new_text, joke_id))
            conn.commit()
            
            if cursor.rowcount > 0:
                await query.edit_message_text(f"Joke #{joke_id} has been updated with new text:\n{new_text}")
                await context.bot.send_message(chat_id=user_id, text=f"Your request to change joke #{joke_id} has been approved.")
            else:
                await query.edit_message_text(f"Error: Joke #{joke_id} not found.")
                await context.bot.send_message(chat_id=user_id, text=f"Error: Joke #{joke_id} not found.")
                
            cursor.close()
            conn.close()
            
        elif command == "clear":
            # Очищаем базу данных
            conn = joke_manager.get_db()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM jokes")
            conn.commit()
            cursor.close()
            conn.close()
            
            await query.edit_message_text("Database has been cleared!")
            await context.bot.send_message(chat_id=user_id, text="Your request to clear the database has been approved.")
    
    else:  # decline
        # Уведомляем администратора и пользователя
        await query.edit_message_text(f"Request declined: {command}")
        await context.bot.send_message(chat_id=user_id, text=f"Sorry, your {command} request was not approved.")

# Добавляем команду для изменения шутки
async def change_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Enter joke ID to change:")
    return JOKE_ID

# Обработчик ввода ID шутки для изменения
async def change_joke_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        joke_id = int(update.message.text)
        context.user_data['joke_id'] = joke_id
        
        # Проверяем, существует ли шутка с таким ID
        conn = joke_manager.get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, text FROM jokes WHERE id = %s", (joke_id,))
        joke = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if joke:
            await update.message.reply_text(f"Current joke text: {joke[1]}\n\nEnter new text for the joke:")
            return NEW_JOKE
        else:
            await update.message.reply_text(f"Error: Joke with ID {joke_id} not found.")
            return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("Please enter a valid number.")
        return JOKE_ID

# Обработчик ввода нового текста шутки
async def change_new_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_text = update.message.text
    joke_id = context.user_data.get('joke_id')
    user_id = update.effective_user.id
    
    # Отправляем на модерацию
    await send_for_moderation(
        context=context,
        user_id=user_id,
        command_type="change",
        payload={'joke_id': joke_id, 'new_text': new_text},
        message=update.message
    )
    
    return ConversationHandler.END

# Главная функция
def main():
    # Создание приложения БЕЗ прокси
    application = ApplicationBuilder().token(TG_TOKEN).build()
    
    # Установка меню команд - используем post_init вместо create_task
    application.post_init = setup_commands
    
    # Добавление обработчиков команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("show", show))
    
    # Обработчик для кнопок выбора категории
    application.add_handler(CallbackQueryHandler(show_category_callback, pattern="^show_"))
    
    # Обработчик разговора для добавления шутки
    add_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("add", add_start)],
        states={
            CATEGORY: [CallbackQueryHandler(add_category_callback, pattern="^add_")],
            JOKE_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_joke_text)],
        },
        fallbacks=[],
    )
    application.add_handler(add_conv_handler)
    application.add_handler(CallbackQueryHandler(add_category_callback, pattern="^add_"))
    
    # Обработчик разговора для удаления шутки
    delete_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("delete", delete_start)],
        states={
            JOKE_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, delete_joke_id)],
            CATEGORY: [CallbackQueryHandler(delete_category_callback, pattern="^delete_")],
        },
        fallbacks=[],
    )
    application.add_handler(delete_conv_handler)
    
    # Добавляем скрытую команду clear
    application.add_handler(CommandHandler("clear", clear_database))
    
    # Обработчик для кнопок модерации
    application.add_handler(CallbackQueryHandler(process_admin_decision, pattern="^(approve|decline)_"))
    
    # Обработчик разговора для изменения шутки
    change_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("change", change_start)],
        states={
            JOKE_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, change_joke_id)],
            NEW_JOKE: [MessageHandler(filters.TEXT & ~filters.COMMAND, change_new_text)],
        },
        fallbacks=[],
    )
    application.add_handler(change_conv_handler)
    
    # Запуск бота
    application.run_polling()

if __name__ == "__main__":
    main() 