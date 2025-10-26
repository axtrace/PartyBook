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
from file_extractor import FileExtractor
from book_adder import BookAdder
from shared_functions import send_portion

# Получаем токен бота из переменных окружения (для тестирования или для продакшена)
token = os.environ['TOKEN']

bot = telebot.TeleBot(token)

s3a = s3_adapter.s3Adapter()
book_reader = BookReader()
books_library = BooksLibrary()
file_extractor = FileExtractor()
book_adder = BookAdder()

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

def auto_send_handler(event, context):
    """
    Обработчик для триггера автопересылки
    """
    from auto_sender import AutoSender
    from datetime import datetime
    
    print(f"🔄 Получен триггер автопересылки: {event}")
    
    try:
        auto_sender = AutoSender()
        current_time = datetime.now()
        result = auto_sender.process_auto_send(current_time)
        
        print(f"✅ Автопересылка завершена: {result}")
        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }
    except Exception as e:
        print(f"❌ Ошибка автопересылки: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def telegram_handler(event, context):
    """
    Обработчик для сообщений Telegram
    """
    message = telebot.types.Update.de_json(event['body'])
    bot.process_new_updates([message])
    return {
        'statusCode': 200,
        'body': 'OK'
    }


def handler(event, context):
    """
    Главный обработчик - определяет тип события и направляет в соответствующий handler
    """
    # Проверяем, это ли триггер автопересылки
    if 'trigger_type' in event and event['trigger_type'] == 'timer':
        return auto_send_handler(event, context)
    
    # Обычная обработка сообщений Telegram
    return telegram_handler(event, context)

@bot.message_handler(commands=['start'])
def start_handler(message):
    try:
        user_id, chat_id = message.from_user.id, message.chat.id
        lang = books_library.get_lang(user_id)
        if lang not in config.message_success_start:
            lang = 'ru'  # Fallback на русский язык
        msg = config.message_success_start[lang]
        bot.send_message(chat_id, msg,
                        reply_markup=markup(['/poem_mode', '/help']))
    except Exception as e:
        bot.reply_to(message, e)

@bot.message_handler(commands=['more'])
def more_handler(message):
    try:
        user_id, chat_id = message.from_user.id, message.chat.id
        send_portion(user_id, chat_id, bot)
        # bot.reply_to(message, "more", reply_markup=user_markup_normal)
    except Exception as e:
        bot.reply_to(message, f"⚠️ Ошибка: {str(e)}")

@bot.message_handler(commands=['help'])
def help_handler(message):
    try:
        user_id, chat_id = message.from_user.id, message.chat.id
        bot.send_chat_action(chat_id, 'typing')
        lang = books_library.get_lang(user_id)
        if lang not in config.message_help:
            lang = 'ru'  # Fallback на русский язык
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
        if lang not in config.message_everyday_ON:
            lang = 'ru'  # Fallback на русский язык
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
            if lang not in config.error_current_book:
                lang = 'ru'  # Fallback на русский язык
            msg = config.error_current_book[lang]
            bot.send_message(chat_id, msg, reply_markup=user_markup_normal)
            return
            
        # Переключаем режим: normal <-> poem
        new_mode = "poem" if current_mode == "normal" else "normal"
        books_library.update_book_mode(user_id, book_id, new_mode)
        
        lang = books_library.get_lang(user_id)
        if lang not in config.message_poem_mode_ON:
            lang = 'ru'  # Fallback на русский язык
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
            if new_lang not in config.message_lang_changed:
                new_lang = 'ru'  # Fallback на русский язык
            msg = config.message_lang_changed[new_lang]
        else:
            if cur_lang not in config.error_lang_recognition:
                cur_lang = 'ru'  # Fallback на русский язык
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

@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_text(message):
    try:
        bot.reply_to(message, "privet-privet", reply_markup=user_markup_normal)
    except Exception as e:
        bot.reply_to(message, f"⚠️ Ошибка: {str(e)}")


# Функции send_portion, book_finished, turn_off_autostatus теперь импортируются из shared_functions


def books_list_message(books_list, user_id):
    # prepare message and keyboard by list of user's books
        lang = books_library.get_lang(user_id)
        if lang not in config.message_empty_booklist:
            lang = 'ru'  # Fallback на русский язык
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
        if lang not in config.message_now_reading:
            lang = 'ru'  # Fallback на русский язык
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
        if lang not in config.error_current_book:
            lang = 'ru'  # Fallback на русский язык
        return config.error_current_book[lang]
    return book_name


@bot.message_handler(content_types=['document'])
def handle_document(message):
    try:
        user_id, chat_id = message.from_user.id, message.chat.id
        lang = books_library.get_lang(user_id)
        path_for_save = config.path_for_save
        
        print(f"📄 Получен документ от пользователя {user_id}: {message.document.file_name}")
        
        bot.send_chat_action(chat_id, 'typing')
        
        # Скачиваем файл локально
        local_file_path = file_extractor.local_save_file(bot, message, path_for_save)
        print(f"📁 Файл сохранен: {local_file_path}")
        
        if local_file_path != -1:
            # Обрабатываем файл и создаем чанки в БД
            # Для новых книг используем режим 'by_sense' по умолчанию
            sending_mode = 'by_sense'
            print(f"🔄 Начинаем обработку файла с режимом: {sending_mode}")
            
            # Используем новый параллельный метод обработки
            book_id = book_adder.add_new_book_parallel(user_id, chat_id, local_file_path, sending_mode, bot)
            print(f"📚 Книга обработана, ID: {book_id}")
            
            if book_id != -1:
                # Проверяем, что lang - это валидный ключ
                if lang not in config.message_file_added:
                    lang = 'ru'  # Fallback на русский язык
                msg = config.message_file_added[lang]
                bot.send_message(chat_id, msg, reply_markup=user_markup_normal)
                print(f"✅ Книга успешно добавлена для пользователя {user_id}")
            else:
                # Проверяем, что lang - это валидный ключ
                if lang not in config.error_file_processing:
                    lang = 'ru'  # Fallback на русский язык
                msg = config.error_file_processing[lang]
                bot.send_message(chat_id, msg, reply_markup=user_markup_normal)
                print(f"❌ Ошибка обработки файла для пользователя {user_id}")
        else:
            # Проверяем, что lang - это валидный ключ
            if lang not in config.error_file_type:
                lang = 'ru'  # Fallback на русский язык
            msg = config.error_file_type[lang]
            bot.send_message(chat_id, msg, reply_markup=user_markup_normal)
            print(f"❌ Неподдерживаемый тип файла: {message.document.file_name}")
    except Exception as e:
        print(f"❌ Критическая ошибка в handle_document: {str(e)}")
        bot.reply_to(message, f"⚠️ Ошибка: {str(e)}")


def _get_user_send_mode(user_id):
    # Получаем режим текущей книги пользователя
    book_id, book_name, pos, mode = books_library.get_current_book(user_id)
    
    if mode == "poem":
        return 'by_newline'  # Режим стихов - разбивка по строкам
    else:
        return 'by_sense'    # Обычный режим - разбивка по смыслу
