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
ASK_NAME, ASK_FACULTY, ASK_GROUP, ASK_QUESTION, LAB1_OBJECT, LAB1_BENEFIT1, LAB1_BENEFIT2, LAB1_BENEFIT3, LAB1_CONFIRM, LAB1_CHANGE = range(10)

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
        update.message.reply_text("Неправильно. Пожалуйста, напишите свою фамилию, имя и отчество в формате: Иванов Иван Иванович.", parse_mode=ParseMode.HTML)
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
    update.message.reply_text("Итак, чем я могу вам помочь? 🐭", parse_mode=ParseMode.HTML)
    show_main_menu(update)
    return ConversationHandler.END

# Отображение главного меню
def show_main_menu(update: Update):
    reply_markup = ReplyKeyboardMarkup([
        [KeyboardButton('🔎 Найти ответ на вопрос')],
        [KeyboardButton('🔬 Помочь с лабораторными')]
    ], resize_keyboard=True)
    update.message.reply_text("Выберите действие:", reply_markup=reply_markup, parse_mode=ParseMode.HTML)

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
    update.message.reply_text("Здесь представлены три лабораторные работы. Ваша задача - выполнить их все. После этого, я помогу вам оформить отчет для отправки преподавателю.", parse_mode=ParseMode.HTML)
    update.message.reply_text("Выберите номер лабораторной работы, используя кнопку ниже. ⬇️", reply_markup=get_lab_work_keyboard(), parse_mode=ParseMode.HTML)

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
        query.edit_message_text(text="Вы выбрали Лабораторная работа №1.", parse_mode=ParseMode.HTML)
        # Отправка сообщений, связанных с лабораторной работой №1
        context.bot.send_chat_action(chat_id=query.message.chat_id, action=ChatAction.TYPING)
        time.sleep(1.5)
        context.bot.send_photo(chat_id=query.message.chat_id, photo='https://drive.google.com/uc?export=view&id=1zv_PACb5zO436uyR-wsA2-ldezXgjy_A', caption="Вам необходимо провести анализ личного вклада в сокращение процента захораниваемых отходов. Данный анализ включает 3 пункта:", parse_mode=ParseMode.HTML)

        time.sleep(1.5)
        context.bot.send_chat_action(chat_id=query.message.chat_id, action=ChatAction.TYPING)
        time.sleep(2)
        context.bot.send_message(chat_id=query.message.chat_id, text="1. Проведите анализ возможности реализации раздельного сбора Вами лично на примере любого объекта, заполните Таблицу 1. Вы можете выбрать: дом, квартиру, дачу, общежитие, или даже ваше место работы, если оно конечно уже есть.\n2. Используя <a href='https://recyclemap.ru/'>https://recyclemap.ru/</a> (если ваш город есть в данном сервисе) или другой доступный вам ресурс, найдите ближайшие к вам точки раздельного сбора. Заполните Таблицу 2, указав точки и виды отходов, которые вы разделяете/сдаете или могли бы это делать в своем городе.\n3. Уже зная состав своей мусорной корзины, используйте пять простых принципов (5R), которые лежат в основе безотходного образа жизни и заполните таблицу 3. Постарайтесь не оставлять пустых ячеек в столбце “Могу делать в будущем”, вы наверняка можете больше, чем кажется.", parse_mode=ParseMode.HTML)

        time.sleep(1.5)
        context.bot.send_chat_action(chat_id=query.message.chat_id, action=ChatAction.TYPING)
        time.sleep(2)
        context.bot.send_photo(chat_id=query.message.chat_id, photo='https://drive.google.com/uc?export=view&id=1Ua7RYLVDSdQYfpViCqn8Ok8AqD1syteQ', caption="Начнем с таблицы № 1 – Анализ возможности реализации раздельного сбора.", parse_mode=ParseMode.HTML)

        time.sleep(1.5)
        context.bot.send_chat_action(chat_id=query.message.chat_id, action=ChatAction.TYPING)
        time.sleep(2)
        context.bot.send_message(chat_id=query.message.chat_id, text="Укажите <b>объект</b>, который вы будете анализировать", parse_mode=ParseMode.HTML)
        return LAB1_OBJECT
    elif selected_lab == 'lab2':
        query.edit_message_text(text="Вы выбрали Лабораторная работа №2.", parse_mode=ParseMode.HTML)
        show_main_menu(query.message)
    elif selected_lab == 'lab3':
        query.edit_message_text(text="Вы выбрали Лабораторная работа №3.", parse_mode=ParseMode.HTML)
        show_main_menu(query.message)

# Обработка выбора объекта для лабораторной работы №1
def lab1_object(update: Update, context: CallbackContext) -> int:
    user_id = update.effective_user.id
    user_data = user_data_manager.get_user_data(user_id)
    user_data['lab1_object'] = update.message.text
    user_data_manager.update_user_data(user_id, user_data)

    context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    time.sleep(1.5)
    update.message.reply_text("Переходим к первому вопросу – <b>Какие выгоды (экономические, социальные, экологические) вы и все участники процесса смогут получить благодаря раздельному сбору на выбранном объекте?</b>\nУкажите первый пункт из трех 👇", parse_mode=ParseMode.HTML)
    return LAB1_BENEFIT1

# Обработка первого пункта выгоды для лабораторной работы №1
def lab1_benefit1(update: Update, context: CallbackContext) -> int:
    user_id = update.effective_user.id
    user_data = user_data_manager.get_user_data(user_id)
    user_data['lab1_benefit1'] = update.message.text
    user_data_manager.update_user_data(user_id, user_data)

    context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    time.sleep(1.5)
    update.message.reply_text("Хорошо 👌 Укажите второй пункт из трех 👇", parse_mode=ParseMode.HTML)
    return LAB1_BENEFIT2

# Обработка второго пункта выгоды для лабораторной работы №1
def lab1_benefit2(update: Update, context: CallbackContext) -> int:
    user_id = update.effective_user.id
    user_data = user_data_manager.get_user_data(user_id)
    user_data['lab1_benefit2'] = update.message.text
    user_data_manager.update_user_data(user_id, user_data)

    context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    time.sleep(1.5)
    update.message.reply_text("Супер 👍 Укажите третий пункт 👇", parse_mode=ParseMode.HTML)
    return LAB1_BENEFIT3

# Обработка третьего пункта выгоды для лабораторной работы №1
def lab1_benefit3(update: Update, context: CallbackContext) -> int:
    user_id = update.effective_user.id
    user_data = user_data_manager.get_user_data(user_id)
    user_data['lab1_benefit3'] = update.message.text
    user_data_manager.update_user_data(user_id, user_data)

    context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    time.sleep(1.5)
    benefits = (
        f"<b>Преимущества:</b>\n"
        f"Пункт 1: {user_data['lab1_benefit1']}\n"
        f"Пункт 2: {user_data['lab1_benefit2']}\n"
        f"Пункт 3: {user_data['lab1_benefit3']}\n"
        f"Если все верно?"
    )
    buttons = [
        [InlineKeyboardButton("Да", callback_data='confirm_yes')],
        [InlineKeyboardButton("Нет", callback_data='confirm_no')],
        [InlineKeyboardButton("Хочу добавить пункт", callback_data='confirm_add')]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    update.message.reply_text(benefits, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    return LAB1_CONFIRM

# Обработка подтверждения преимуществ
def lab1_confirm(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    user_id = query.message.chat_id
    user_data = user_data_manager.get_user_data(user_id)

    if query.data == 'confirm_yes':
        query.edit_message_text(text="Отлично! Лабораторная работа №1 завершена.", parse_mode=ParseMode.HTML)
        show_main_menu(query.message)
        return ConversationHandler.END
    elif query.data == 'confirm_no':
        query.edit_message_text(text="Какой пункт вы хотите изменить? Укажите номер пункта (1, 2 или 3):", parse_mode=ParseMode.HTML)
        return LAB1_CHANGE
    elif query.data == 'confirm_add':
        query.edit_message_text(text="Добавьте еще один пункт:", parse_mode=ParseMode.HTML)
        return LAB1_BENEFIT1

def handle_lab1_confirm_change(update: Update, context: CallbackContext) -> int:
    user_id = update.effective_user.id
    user_data = user_data_manager.get_user_data(user_id)
    change_point = update.message.text.strip()

    if change_point == '1':
        update.message.reply_text("Укажите новый пункт 1:", parse_mode=ParseMode.HTML)
        context.user_data['lab1_edit'] = 'lab1_benefit1'
        return LAB1_BENEFIT1
    elif change_point == '2':
        update.message.reply_text("Укажите новый пункт 2:", parse_mode=ParseMode.HTML)
        context.user_data['lab1_edit'] = 'lab1_benefit2'
        return LAB1_BENEFIT2
    elif change_point == '3':
        update.message.reply_text("Укажите новый пункт 3:", parse_mode=ParseMode.HTML)
        context.user_data['lab1_edit'] = 'lab1_benefit3'
        return LAB1_BENEFIT3

# Отправка уведомлений
def send_notifications(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        update.message.reply_text("Эта функция доступна только для преподавателей.", parse_mode=ParseMode.HTML)
        return

    context.bot.send_message(chat_id=update.effective_chat.id, text="Что нужно отправить? Введите текст, цифры или отправьте изображение.", parse_mode=ParseMode.HTML)
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
        update.message.reply_text(f"Сообщение отправлено {sent_count} пользователям.", parse_mode=ParseMode.HTML)

# Обработка ошибок
def error_handler(update: Update, context: CallbackContext):
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    update.message.reply_text('Произошла ошибка. Пожалуйста, попробуйте еще раз позже.', parse_mode=ParseMode.HTML)

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
            ASK_QUESTION: [MessageHandler(Filters.text & ~Filters.command, handle_question)],
            LAB1_OBJECT: [MessageHandler(Filters.text & ~Filters.command, lab1_object)],
            LAB1_BENEFIT1: [MessageHandler(Filters.text & ~Filters.command, lab1_benefit1)],
            LAB1_BENEFIT2: [MessageHandler(Filters.text & ~Filters.command, lab1_benefit2)],
            LAB1_BENEFIT3: [MessageHandler(Filters.text & ~Filters.command, lab1_benefit3)],
            LAB1_CONFIRM: [
                CallbackQueryHandler(lab1_confirm, pattern='confirm_yes|confirm_no|confirm_add')
            ],
            LAB1_CHANGE: [MessageHandler(Filters.text & ~Filters.command, handle_lab1_confirm_change)]
        },
        fallbacks=[CommandHandler('start', start)],
        per_message=True  # Добавляем per_message=True
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
