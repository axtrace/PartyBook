import json
import telebot
import os
import boto3
import requests
import config
import s3_adapter
from book_reader import BookReader
from books_library import BooksLibrary
from models.user import User
from models.book import Book

# Получаем токен бота из переменных окружения (для тестирования или для продакшена)
token = os.environ['TOKEN']

bot = telebot.TeleBot(token)

s3a = s3_adapter.s3Adapter()
book_reader = BookReader()
books_library = BooksLibrary()

# Список команд для клавиатуры
commands = ['/help', '/more', '/my_books', '/auto_status', '/now_reading',
            '/poem_mode', '/change_lang']

def markup(clist):
    if len(clist) == 0:
        return telebot.types.ReplyKeyboardRemove(True)
    user_markup = telebot.types.ReplyKeyboardMarkup(True,
                                                    one_time_keyboard=True)
    for item in clist:
        user_markup.row(item)
    return user_markup

# Создаем основную клавиатуру
user_markup_normal = markup(commands)

def handler(event, context):
    message = telebot.types.Update.de_json(event['body'])
    bot.process_new_updates([message])
    return {
        'statusCode': 200,
        'body': 'OK'
    }

@bot.message_handler(commands=['start'])
def start_handler(message):
    try:
        user_id, chat_id = message.from_user.id, message.chat.id
        lang = books_library.get_lang(user_id)
        msg = config.message_success_start[lang]
        bot.send_message(chat_id, msg,
                        reply_markup=markup(['/poem_mode', '/help']))
    except Exception as e:
        bot.reply_to(message, e)

@bot.message_handler(commands=['more'])
def more_handler(message):
    try:
        user_id, chat_id = message.from_user.id, message.chat.id
        send_portion(user_id, chat_id)
        # bot.reply_to(message, "more", reply_markup=user_markup_normal)
    except Exception as e:
        bot.reply_to(message, f"⚠️ Ошибка: {str(e)}")

@bot.message_handler(commands=['help'])
def help_handler(message):
    try:
        user_id, chat_id = message.from_user.id, message.chat.id
        bot.send_chat_action(chat_id, 'typing')
        lang = books_library.get_lang(user_id)
        msg = config.message_help[lang]
        bot.send_message(chat_id, msg, reply_markup=user_markup_normal)
    except Exception as e:
        bot.reply_to(message, f"⚠️ Ошибка: {str(e)}")

@bot.message_handler(commands=['my_books'])
def my_books_handler(message):
    try:
        user_id, chat_id = message.from_user.id, message.chat.id
        bot.send_chat_action(chat_id, 'typing')
        books_list = books_library.get_user_books(user_id)
        msg, user_markup = books_list_message(books_list, user_id)
        bot.send_message(chat_id, msg, reply_markup=user_markup)
        bot.register_next_step_handler(message, process_change_book)
    except Exception as e:
        bot.reply_to(message, f"⚠️ Ошибка: {str(e)}")

@bot.message_handler(commands=['auto_status'])
def auto_status_handler(message):
    try:
        user_id, chat_id = message.from_user.id, message.chat.id
        lang = books_library.get_lang(user_id)
        # 1 means auto is ON
        is_auto_ON = (books_library.get_auto_status(user_id) == 1)
        markup_list = ['/more', '/help']
        if is_auto_ON:
            markup_list.append('/stop_auto')
            msg = config.message_everyday_ON[lang]
        else:
            markup_list.append('/start_auto')
            msg = config.message_everyday_OFF[lang]
        bot.send_message(chat_id, msg, reply_markup=markup(markup_list))
    except Exception as e:
        bot.reply_to(message, f"⚠️ Ошибка: {str(e)}")

@bot.message_handler(commands=['now_reading'])
def now_reading_handler(message):
    try:
        user_id, chat_id = message.from_user.id, message.chat.id
        bot.send_chat_action(chat_id, 'typing')
        book_name = now_reading_answer(user_id)
        bot.send_message(chat_id, book_name,
                        reply_markup=user_markup_normal)
    except Exception as e:
        bot.reply_to(message, f"⚠️ Ошибка: {str(e)}")

@bot.message_handler(commands=['poem_mode'])
def poem_mode_handler(message):
    try:
        user_id, chat_id = message.from_user.id, message.chat.id
        bot.send_chat_action(chat_id, 'typing')
        
        # Получаем текущую книгу пользователя
        book_id, book_name, pos, current_mode = books_library.get_current_book(user_id)
        
        if book_id is None or book_name is None:
            lang = books_library.get_lang(user_id)
            msg = config.error_current_book[lang]
            bot.send_message(chat_id, msg, reply_markup=user_markup_normal)
            return
            
        # Переключаем режим: normal <-> poem
        new_mode = "poem" if current_mode == "normal" else "normal"
        books_library.update_book_mode(user_id, book_id, new_mode)
        
        lang = books_library.get_lang(user_id)
        if new_mode == "poem":
            msg = config.message_poem_mode_ON[lang]
        else:
            msg = config.message_poem_mode_OFF[lang]
            
        bot.send_message(chat_id, msg, reply_markup=user_markup_normal)
    except Exception as e:
        bot.reply_to(message, f"⚠️ Ошибка: {str(e)}")

@bot.message_handler(commands=['change_lang'])
def change_lang_handler(message):
    try:
        user_id, chat_id = message.from_user.id, message.chat.id
        lang_list = ['en', 'ru']
        msg = 'Choose language on keyboard\n'
        bot.send_message(chat_id, msg, reply_markup=markup(lang_list))
        bot.register_next_step_handler(message, change_lang)
    except Exception as e:
        bot.reply_to(message, f"⚠️ Ошибка: {str(e)}")


def change_lang(message):
    try:
        user_id, chat_id = message.from_user.id, message.chat.id
        cur_lang = books_library.get_lang(user_id)
        new_lang = message.text
        lang_list = ['en', 'ru']
        
        if new_lang in lang_list:
            books_library.update_lang(user_id, new_lang)
            msg = config.message_lang_changed[new_lang]
        else:
            msg = config.error_lang_recognition[cur_lang]
        bot.send_message(chat_id, msg, reply_markup=user_markup_normal)
    except Exception as e:
        bot.reply_to(message, f"⚠️ Ошибка: {str(e)}")

@bot.message_handler(commands=['stop_auto', 'start_auto'])
def change_autostatus(message):
    try:
        user_id = message.from_user.id
        # 1 means auto is ON
        if switch_needed(message):
            books_library.switch_auto_status(user_id)
        auto_status_handler(message)  # Show updated status
    except Exception as e:
        bot.reply_to(message, f"⚠️ Ошибка: {str(e)}")

@bot.message_handler(content_types=['document'])
def handle_document(message):
    try:
        bot.reply_to(message, "document", reply_markup=user_markup_normal)
    except Exception as e:
        bot.reply_to(message, f"⚠️ Ошибка: {str(e)}")

@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_text(message):
    try:
        bot.reply_to(message, "privet-privet", reply_markup=user_markup_normal)
    except Exception as e:
        bot.reply_to(message, f"⚠️ Ошибка: {str(e)}")


def book_finished(portion):
    if config.end_book_string in portion:
        return True
    if portion == '/more':
        return True
    return False

def turn_off_autostatus(user_id, chat_id):
    # turn off autostatus if book was finished
    if books_library.get_auto_status(user_id):
        books_library.switch_auto_status(user_id)
        lang = books_library.get_lang(user_id)
        auto_off_msg = config.message_everyday_OFF[lang]
        user_markup = markup(['/start_auto', '/my_books'])
        bot.send_message(chat_id, auto_off_msg, reply_markup=user_markup)


def send_portion(user_id, chat_id):
    try:
        bot.send_chat_action(chat_id, 'typing')
        lang = books_library.get_lang(user_id) # todo: перейти на модель User.lang
        msg = book_reader.get_next_portion(user_id)
        
        if msg is None:
            msg = config.error_user_finding[lang]
            bot.send_message(chat_id, msg)
            return -1
            
        if book_finished(msg):
            finished_text = config.message_book_finished[lang]
            msg += f"\n{finished_text}\n/start_auto\n/my_books"
            turn_off_autostatus(user_id, chat_id)
        else:
            msg += '\n/more'
            
        # Отправляем сообщение. Если сообщение слишком длинное — делим на части
        max_telegram_size = 4096
        for i in range(0, len(msg), max_telegram_size):
            bot.send_message(chat_id, msg[i:i+max_telegram_size], reply_markup=markup([]))
            
        return 0
    except Exception as e:
        bot.send_message(chat_id, f"Error: {str(e)}")
        return -1


def books_list_message(books_list, user_id):
    # prepare message and keyboard by list of user's books
    lang = books_library.get_lang(user_id)
    if len(books_list) == 0:
        msg = config.message_empty_booklist[lang]
        return msg, markup(['/help'])
    msg = str(config.message_booklist[lang])
    markup_list = []
    for book in books_list:
        msg += '\t' + str(book).replace(str(user_id) + '_', '') + '\n'
        markup_list.append('/' + str(book).replace(str(user_id) + '_', ''))
    msg += str(config.message_choose_book[lang])
    return msg, markup(markup_list)


def process_change_book(message):
    try:
        user_id, chat_id = message.from_user.id, message.chat.id
        lang = books_library.get_lang(user_id)
        new_book = message.text.replace('/', '')
        new_book = str(user_id) + '_' + new_book
        bot.send_chat_action(chat_id, 'typing')
        books_list = books_library.get_user_books(user_id)
        if new_book in books_list:
            books_library.update_current_book(user_id, chat_id, new_book)
            book_id, book_name, pos, mode = books_library.get_current_book(user_id, is_format_name_needed=True)
            msg = config.message_now_reading[lang].format(book_name)
            bot.send_message(chat_id, msg,
                            reply_markup=markup(['/more', '/help']))
        else:
            msg = config.error_book_recognition[lang]
            bot.send_message(chat_id, msg)
    except Exception as e:
        bot.reply_to(message, f"⚠️ Ошибка: {str(e)}")


def switch_needed(message):
    user_id, chat_id = message.from_user.id, message.chat.id
    is_auto_ON = (books_library.get_auto_status(user_id) == 1)
    command = message.text.replace('/', '')
    # update only if ON+stop OR OFF+start:
    legitimate_stop = is_auto_ON and command == 'stop_auto'
    legitimate_start = not is_auto_ON and command == 'start_auto'
    need = legitimate_stop or legitimate_start
    return need


def now_reading_answer(user_id):
    # prepare answer for now reading.
    # If no info, returns error message from config
    book_id, book_name, pos, mode = books_library.get_current_book(user_id, is_format_name_needed=True)
    if book_name == -1:
        lang = books_library.get_lang(user_id)
        return config.error_current_book[lang]
    return book_name


def _get_user_send_mode(user_id):
    # Получаем режим текущей книги пользователя
    book_id, book_name, pos, mode = books_library.get_current_book(user_id)
    
    if mode == "poem":
        return 'by_newline'  # Режим стихов - разбивка по строкам
    else:
        return 'by_sense'    # Обычный режим - разбивка по смыслу
