import sys
import telebot
from apscheduler.schedulers.background import BackgroundScheduler
import time

import config
import tokens
from book_adder import BookAdder
from book_reader import BookReader
from books_library import BooksLibrary
from file_extractor import FileExtractor
from info_logger import BotLogger

token = tokens.test_token
if '--prod' in sys.argv:
    token = tokens.production_token

book_reader = BookReader()
tb = telebot.TeleBot(token)
book_adder = BookAdder()
books_library = BooksLibrary()
commands = ['/more', '/my_books', '/auto_stasus', '/now_reading',
            '/poem_mode', '/help']

# todo add timestamp to logs
logger = BotLogger()
logger.info('Telebot started')

# remove_markup = telebot.types.ReplyKeyboardHide(True) # for old versions of teelbot
remove_markup = telebot.types.ReplyKeyboardRemove(True)
user_markup_normal = telebot.types.ReplyKeyboardMarkup(True,
                                                       one_time_keyboard=True)
for com in commands:
    user_markup_normal.row(com)

poem_mode_user_id_list = set()  # set of userID which choose poem_mode before sending a book file


@tb.message_handler(commands=['start'])
def start_handler(message):
    try:
        user_id, chat_id = message.from_user.id, message.chat.id
        logger.log_message(message)
        msg = config.success_start_reply
        if books_library.get_current_book(user_id) == -1:
            msg = config.message_hello
        tb.send_message(chat_id, msg, reply_markup=user_markup_normal)
        logger.log_sent(user_id, chat_id, msg)
    except Exception as e:
        tb.reply_to(message, e)
        logger.error(e)


@tb.message_handler(commands=['auto_stasus'])
def view_autostatus(message):
    try:
        user_id, chat_id = message.from_user.id, message.chat.id
        logger.log_message(message)
        # 1 means auto is ON
        is_auto_ON = (books_library.get_auto_status(user_id) == 1)
        user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
        user_markup.row('/more')
        if is_auto_ON:
            user_markup.row('/stop_auto')
            msg = config.message_everyday_ON
        else:
            user_markup.row('/start_auto')
            msg = config.message_everyday_OFF
        tb.send_message(chat_id, msg, reply_markup=user_markup)
        logger.log_sent(user_id, chat_id, msg)
    except Exception as e:
        tb.reply_to(message, e)
        logger.error(e)


@tb.message_handler(commands=['stop_auto', 'start_auto'])
def change_autostatus(message):
    try:
        user_id, chat_id = message.from_user.id, message.chat.id
        # 1 means auto is ON
        logger.log_message(message)
        if switch_needed(message):
            books_library.switch_auto_staus(user_id)
        view_autostatus(message)
    except Exception as e:
        tb.reply_to(message, e)
        logger.error(e)


def switch_needed(message):
    user_id, chat_id = message.from_user.id, message.chat.id
    is_auto_ON = (books_library.get_auto_status(user_id) == 1)
    command = message.text.replace('/', '')
    # update only if ON+stop OR OFF+start:
    legitimate_stop = is_auto_ON and command == 'stop_auto'
    legitimate_start = not is_auto_ON and command == 'start_auto'
    need = legitimate_stop or legitimate_start
    return need


@tb.message_handler(commands=['my_books'])
def show_user_books(message):
    try:
        user_id, chat_id = message.from_user.id, message.chat.id
        logger.log_message(message)
        tb.send_chat_action(chat_id, 'typing')
        books_list = books_library.get_user_books(user_id)
        msg = config.message_booklist
        user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
        for book in books_list:
            msg += str(book).replace(str(user_id) + '_', '') + '\n'
            user_markup.row('/' + str(book).replace(str(user_id) + '_', ''))
        msg += config.message_choose_book
        tb.send_message(chat_id, msg, reply_markup=user_markup)
        logger.log_sent(user_id, chat_id, msg)
        tb.register_next_step_handler(message, process_change_book)
    except Exception as e:
        tb.reply_to(message, e)
        logger.error(e)


def process_change_book(message):
    try:
        user_id, chat_id = message.from_user.id, message.chat.id
        new_book = message.text.replace('/', '')
        new_book = str(user_id) + '_' + new_book
        tb.send_chat_action(chat_id, 'typing')
        books_list = books_library.get_user_books(user_id)
        if new_book in books_list:
            books_library.update_current_book(user_id, chat_id, new_book)
            book_name = books_library.get_current_book(user_id,
                                                       format_name=True)
            msg = config.message_now_reading.format(
                book_name)
            tb.send_message(chat_id, msg,
                            reply_markup=user_markup_normal)
            logger.log_sent(user_id, chat_id, msg)
        else:
            tb.send_message(chat_id, config.error_book_recognition)
            logger.log_sent(user_id, chat_id, config.error_book_recognition)
    except Exception as e:
        tb.reply_to(message, e)
        logger.error(e)


@tb.message_handler(commands=['more'])
def listener(message):
    try:
        user_id, chat_id = message.from_user.id, message.chat.id
        logger.log_message(message)
        next_portion = book_reader.get_next_portion(user_id) + '/more'
        send_portion(user_id, chat_id, next_portion)
    except Exception as e:
        tb.reply_to(message, e)
        logger.error(e)


@tb.message_handler(commands=['help'])
def help_handler(message):
    try:
        user_id, chat_id = message.from_user.id, message.chat.id
        logger.log_message(message)
        tb.send_chat_action(chat_id, 'typing')
        tb.send_message(chat_id, config.message_help,
                        reply_markup=user_markup_normal)
        logger.log_sent(user_id, chat_id, config.message_help)
    except Exception as e:
        tb.reply_to(message, e)
        logger.error(e)


@tb.message_handler(commands=['sayhi'])
def sayhi_handler(message):
    try:
        user_id, chat_id = message.from_user.id, message.chat.id
        logger.log_message(message)
        tb.send_message(chat_id, 'Hi sir!')
        logger.log_sent(user_id, chat_id, 'Hi sir!')
    except Exception as e:
        tb.reply_to(message, e)
        logger.error(e)


@tb.message_handler(commands=['now_reading'])
def now_reading_handler(message):
    try:
        user_id, chat_id = message.from_user.id, message.chat.id
        tb.send_chat_action(chat_id, 'typing')
        logger.log_message(message)
        book_name = now_reading_answer(user_id)
        tb.send_message(chat_id, book_name,
                        reply_markup=user_markup_normal)
        logger.log_sent(user_id, chat_id, book_name)
    except Exception as e:
        tb.reply_to(message, e)
        logger.error(e)


def now_reading_answer(user_id):
    # prepare answer for now reading.
    # If no info, returns error message from config
    book_name = books_library.get_current_book(user_id, format_name=True)
    if book_name == -1:
        return config.error_current_book
    return book_name


@tb.message_handler(commands=['poem_mode'])
def poem_mode_handler(message):
    try:
        user_id, chat_id = message.from_user.id, message.chat.id
        poem_mode_user_id_list.add(user_id)
        logger.info('Received message.', 'user_id, chat_id', user_id, chat_id,
                    message.text)
        tb.send_chat_action(chat_id, 'typing')
        tb.send_message(chat_id, config.message_poem_mode_ON,
                        reply_markup=remove_markup)
        logger.log_sent(user_id, chat_id, config.message_poem_mode_ON)
    except Exception as e:
        tb.reply_to(message, e)
        logger.error(e)


def _get_user_send_mode(user_id):
    user_send_mode = 'by_sense'
    if user_id in poem_mode_user_id_list:
        # if user set poem_mode, remember it and delete from query
        user_send_mode = 'by_newline'
        poem_mode_user_id_list.remove(user_id)
    return user_send_mode


@tb.message_handler(content_types=['document'])
def handle_document(message):
    try:
        user_id, chat_id = message.from_user.id, message.chat.id
        logger.log_message(message)
        path_for_save = config.path_for_save
        file_extractor = FileExtractor()
        local_file_path = file_extractor.local_save_file(tb, message,
                                                         path_for_save)
        if (local_file_path != -1):
            book_adder.add_new_book(user_id, chat_id, local_file_path,
                                    sending_mode=_get_user_send_mode(user_id))
            tb.send_message(chat_id, config.success_file_added,
                            reply_markup=remove_markup)
            logger.log_sent(user_id, chat_id, config.success_file_added)
        else:
            tb.send_message(chat_id, config.error_file_type)
    except Exception as e:
        tb.reply_to(message, e)
        logger.error(e)


@tb.message_handler(func=lambda message: True, content_types=['text'])
def command_default(message):
    # this is the standard reply to a normal message
    user_id, chat_id = message.from_user.id, message.chat.id
    logger.log_message(message)
    msg = config.message_dont_understand.format(message.text)
    tb.send_message(chat_id, msg)
    logger.log_sent(user_id, chat_id, msg)


def book_finished(portion):
    if config.end_book_string in portion:
        return True
    if portion == '/more':
        return True
    return False


def turn_off_autostatus(user_id, chat_id):
    # turn off autostatus if book was finished
    if books_library.get_auto_status(user_id):
        books_library.switch_auto_staus(user_id)
        auto_off_msg = config.message_everyday_OFF
        user_markup = telebot.types.ReplyKeyboardMarkup(True,
                                                        False)
        user_markup.row('/start_auto')
        user_markup.row('/my_books')
        tb.send_message(chat_id, auto_off_msg,
                        reply_markup=user_markup)


def send_portion(user_id, chat_id, portion):
    logger.info('Sending to user_id, chat_id: ', user_id, chat_id, 'Message:',
                portion)
    tb.send_chat_action(chat_id, 'typing')
    tb.send_message(chat_id, portion, reply_markup=remove_markup)
    logger.info('OK')
    if book_finished(portion):
        msg = config.message_book_finished + '/n /start_auto' + '/n /my_books'
        turn_off_autostatus(user_id, chat_id)
        tb.send_message(chat_id, msg)


def auto_send_portions():
    send_list = books_library.get_users_for_autosend()
    for item in send_list:
        try:
            user_id, chat_id = item[0], item[1]
            next_portion = book_reader.get_next_portion(user_id) + '/more'
            send_portion(user_id, chat_id, next_portion)
        except Exception as e:
            logger.error(e)
    return 0


if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    scheduler.add_job(auto_send_portions, 'cron', hour=20, minute=20)
    scheduler.start()
    while True:
        try:
            tb.polling(none_stop=True)
        except Exception as e:
            logger.error(e)
            time.sleep(15)
