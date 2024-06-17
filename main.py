import os
import time
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ParseMode, ChatAction, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler, CallbackQueryHandler
import re
import json
import logging

# Включение логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Загрузка переменных из .env файла
load_dotenv()
TOKEN = os.getenv('TELEGRAM_TOKEN')
ADMIN_IDS = list(map(int, os.getenv('ADMIN_IDS').split(',')))

# Проверка наличия токена
if not TOKEN or not ADMIN_IDS:
    raise ValueError("Необходимо указать TELEGRAM_TOKEN и ADMIN_IDS в файле .env")

# Пути к файлам
USER_DATA_FILE = 'user_data.json'
PHOTO_PATH = 'ekolina.jpg'

# Константы для состояний
ASK_NAME, ASK_FACULTY, ASK_GROUP, ASK_QUESTION = range(4)

# Класс для работы с данными пользователей
class UserDataManager:
    def __init__(self, file_path):
        self.file_path = file_path
        self.user_data = self.load_user_data()

    def load_user_data(self):
        if os.path.exists(self.file_path):
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def save_user_data(self):
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(self.user_data, f, ensure_ascii=False, indent=4)

    def get_user_data(self, user_id):
        return self.user_data.get(str(user_id), {})

    def update_user_data(self, user_id, data):
        self.user_data[str(user_id)] = data
        self.save_user_data()

user_data_manager = UserDataManager(USER_DATA_FILE)

# Проверка формата ФИО
def check_full_name(full_name):
    pattern = r'^[А-ЯЁ][а-яё]+ [А-ЯЁ][а-яё]+ [А-ЯЁ][а-яё]+$'
    return re.match(pattern, full_name)

# Начало общения с пользователем
def start(update: Update, context: CallbackContext) -> int:
    user_id = update.effective_user.id
    if str(user_id) in user_data_manager.user_data:
        update.message.reply_text("Итак, чем я могу вам помочь? 🐭")
        show_main_menu(update)
        return ConversationHandler.END

    greeting_text = (
        "<b>Привет</b> 👋\n\n"
        "Меня зовут Эколина. Я образовательный бот факультета экотехнологий университета ИТМО. "
        "Давайте познакомимся 🤩\n"
        "Как тебя зовут? Напиши, пожалуйста, свою фамилию, имя и отчество."
    )
    context.bot.send_photo(chat_id=update.effective_chat.id, photo=open(PHOTO_PATH, 'rb'), caption=greeting_text, parse_mode=ParseMode.HTML)
    return ASK_NAME

# Обработка имени пользователя
def ask_name(update: Update, context: CallbackContext) -> int:
    user_id = update.effective_user.id
    name = update.message.text

    if check_full_name(name):
        user_data = user_data_manager.get_user_data(user_id)
        user_data['name'] = name
        user_data_manager.update_user_data(user_id, user_data)
        update.message.reply_text("<b>Приятно познакомиться</b> 😊 А теперь укажите свой факультет 👇", parse_mode=ParseMode.HTML)
        return ASK_FACULTY
    else:
        update.message.reply_text("Неправильно. Пожалуйста, напишите свою фамилию, имя и отчество в формате: Иванов Иван Иванович.")
        return ASK_NAME

# Обработка факультета пользователя
def ask_faculty(update: Update, context: CallbackContext) -> int:
    user_id = update.effective_user.id
    faculty = update.message.text

    user_data = user_data_manager.get_user_data(user_id)
    user_data['faculty'] = faculty
    user_data_manager.update_user_data(user_id, user_data)
    update.message.reply_text("<b>Класс</b> 👍 Напишите номер своей группы, например G4150 👇", parse_mode=ParseMode.HTML)
    return ASK_GROUP

# Обработка группы пользователя
def ask_group(update: Update, context: CallbackContext) -> int:
    user_id = update.effective_user.id
    group = update.message.text

    user_data = user_data_manager.get_user_data(user_id)
    user_data['group'] = group
    user_data_manager.update_user_data(user_id, user_data)
    update.message.reply_text("Итак, чем я могу вам помочь? 🐭")
    show_main_menu(update)
    return ConversationHandler.END

# Отображение главного меню
def show_main_menu(update: Update):
    reply_markup = ReplyKeyboardMarkup([
        [KeyboardButton('🔎 Найти ответ на вопрос')],
        [KeyboardButton('🔬 Помочь с лабораторными')]
    ], resize_keyboard=True)
    update.message.reply_text("Выберите действие:", reply_markup=reply_markup)

# Обработка кнопки "Найти ответ на вопрос"
def ask_question(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Задавай свой вопрос, а я пролистаю весь интернет, чтобы ответить 🔎\n"
                              "*Мой ИИ может допускать ошибки, поэтому рекомендую проверять важную информацию*", parse_mode=ParseMode.HTML)
    return ASK_QUESTION

# Обработка вопроса пользователя
def handle_question(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Извините, но функция поиска ответов временно недоступна. Пожалуйста, попробуйте позже.", parse_mode=ParseMode.HTML)
    show_main_menu(update)
    return ConversationHandler.END

# Обработка кнопки "Помочь с лабораторными"
def handle_lab_work(update: Update, context: CallbackContext):
    update.message.reply_text("<b>Добро пожаловать в мир лабораторных работ</b> 🙂", parse_mode=ParseMode.HTML)
    update.message.reply_text("Здесь представлены три лабораторные работы. Ваша задача - выполнить их все. После этого, я помогу вам оформить отчет для отправки преподавателю.")
    update.message.reply_text("Выберите номер лабораторной работы, используя кнопку ниже. ⬇️", reply_markup=get_lab_work_keyboard())

# Получение клавиатуры с лабораторными работами
def get_lab_work_keyboard():
    keyboard = [
        [InlineKeyboardButton("Лабораторная работа №1", callback_data='lab1')],
        [InlineKeyboardButton("Лабораторная работа №2", callback_data='lab2')],
        [InlineKeyboardButton("Лабораторная работа №3", callback_data='lab3')]
    ]
    return InlineKeyboardMarkup(keyboard)

# Обработка выбора лабораторной работы
def lab_work_selection(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    selected_lab = query.data

    if selected_lab == 'lab1':
        query.edit_message_text(text="Вы выбрали Лабораторная работа №1.")
    elif selected_lab == 'lab2':
        query.edit_message_text(text="Вы выбрали Лабораторная работа №2.")
    elif selected_lab == 'lab3':
        query.edit_message_text(text="Вы выбрали Лабораторная работа №3.")
    
    # Возврат в главное меню после выбора лабораторной работы
    show_main_menu(update)

# Отправка уведомлений
def send_notifications(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        update.message.reply_text("Эта функция доступна только для преподавателей.")
        return

    context.bot.send_message(chat_id=update.effective_chat.id, text="Что нужно отправить? Введите текст, цифры или отправьте изображение.")
    context.user_data['awaiting_notification'] = True

def handle_notification(update: Update, context: CallbackContext):
    if context.user_data.get('awaiting_notification'):
        notification_content = update.message.caption if update.message.caption else update.message.text
        photo_file_id = update.message.photo[-1].file_id if update.message.photo else None
        sent_count = 0

        for user_id in user_data_manager.user_data.keys():
            if int(user_id) not in ADMIN_IDS:
                if photo_file_id:
                    context.bot.send_photo(chat_id=int(user_id), photo=photo_file_id, caption=notification_content, parse_mode=ParseMode.HTML)
                elif notification_content:
                    context.bot.send_message(chat_id=int(user_id), text=notification_content, parse_mode=ParseMode.HTML)
                sent_count += 1

        context.user_data['awaiting_notification'] = False
        # Отправка уведомления администратору
        update.message.reply_text(f"Сообщение отправлено {sent_count} пользователям.")

# Обработка ошибок
def error_handler(update: Update, context: CallbackContext):
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    update.message.reply_text('Произошла ошибка. Пожалуйста, попробуйте еще раз позже.')

def main():
    updater = Updater(TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # Обработчик команды /start
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ASK_NAME: [MessageHandler(Filters.text & ~Filters.command, ask_name)],
            ASK_FACULTY: [MessageHandler(Filters.text & ~Filters.command, ask_faculty)],
            ASK_GROUP: [MessageHandler(Filters.text & ~Filters.command, ask_group)],
            ASK_QUESTION: [MessageHandler(Filters.text & ~Filters.command, handle_question)]
        },
        fallbacks=[CommandHandler('start', start)]
    )
    dispatcher.add_handler(conv_handler)

    # Обработчик кнопок
    dispatcher.add_handler(MessageHandler(Filters.regex('^🔎 Найти ответ на вопрос$'), ask_question))
    dispatcher.add_handler(MessageHandler(Filters.regex('^🔬 Помочь с лабораторными$'), handle_lab_work))
    dispatcher.add_handler(CallbackQueryHandler(lab_work_selection, pattern='^lab[1-3]$'))
    dispatcher.add_handler(CommandHandler('notify', send_notifications))
    dispatcher.add_handler(CommandHandler('stop_notify', handle_notification))
    dispatcher.add_handler(MessageHandler(Filters.text | Filters.photo, handle_notification))
    dispatcher.add_error_handler(error_handler)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
