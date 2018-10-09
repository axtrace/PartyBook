import os
import sys
import logging
import telebot
from apscheduler.schedulers.background import BackgroundScheduler

import time
import config
import book_reader
import tokens
from text_transliter import TextTransliter
from book_adder import *
from file_extractor import *

token = tokens.test_token
if '--prod' in sys.argv:
    token = tokens.production_token

fh = book_reader.FileHandler()
tb = telebot.TeleBot(token)
book_adder = BookAdder()
commands = ['/more', '/my_books', '/auto_stasus', '/now_reading',
            '/poem_mode', '/help']

# todo add timestamp to logs
logging.basicConfig(filename="sample.log", filemode="w",
                    level=logging.ERROR)
logger = logging.getLogger("ex")

# remove_markup = telebot.types.ReplyKeyboardHide(True)
remove_markup = telebot.types.ReplyKeyboardRemove(True)
user_markup_normal = telebot.types.ReplyKeyboardMarkup(True,
                                                       one_time_keyboard=True)
for com in commands:
    user_markup_normal.row(com)

poem_mode_userId_list = set()  # set of userID which choose poem_mode before sending a book file


@tb.message_handler(commands=['start'])
def start_handler(message):
    try:
        user_id = message.from_user.id
        chat_id = message.chat.id
        if fh.db.get_current_book(user_id) == -1:
            tb.send_message(chat_id, config.message_hello)
        else:
            tb.send_message(chat_id, config.success_start_reply,
                            reply_markup=user_markup_normal)
    except Exception as e:
        tb.reply_to(message, e)


@tb.message_handler(commands=['auto_stasus'])
def auto_send_view_status(message):
    try:
        userId = message.from_user.id
        chatid = message.chat.id
        # 1 means auto is ON
        is_auto_ON = (fh.db.get_auto_status(userId) == 1)
        user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
        user_markup.row('/more')
        if is_auto_ON:
            user_markup.row('/stop_auto')
            msg = config.message_everyday_ON
        else:
            user_markup.row('/start_auto')
            msg = config.message_everyday_OFF
        tb.send_message(chatid, msg, reply_markup=user_markup)
    except Exception as e:
        tb.reply_to(message, e)


@tb.message_handler(commands=['stop_auto', 'start_auto'])
def auto_send_change_status(message):
    try:
        userId = message.from_user.id
        # 1 means auto is ON
        is_auto_ON = (fh.db.get_auto_status(userId) == 1)
        command = message.text.replace('/', '')
        # update only if ON+stop OR OFF+start:
        if (is_auto_ON and command == 'stop_auto') or (
                not is_auto_ON and command == 'start_auto'):
            fh.db.update_auto_status(userId)
        auto_send_view_status(message)
    except Exception as e:
        tb.reply_to(message, e)


@tb.message_handler(commands=['my_books'])
def show_user_books(message):
    try:
        chatid = message.chat.id
        userId = message.from_user.id
        tb.send_chat_action(chatid, 'typing')
        books_list = fh.db.get_user_books(userId)
        answer_text = 'Your books list: ' + '\n'
        user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
        for book in books_list:
            answer_text += str(book).replace(str(userId) + '_',
                                             '') + '\n'
            user_markup.row(
                '/' + str(book).replace(str(userId) + '_', ''))
        answer_text += 'Choose book for start reading'
        tb.send_message(chatid, answer_text, reply_markup=user_markup)
        tb.register_next_step_handler(message, process_change_book)
    except Exception as e:
        tb.reply_to(message, e)


def process_change_book(message):
    try:
        chatid = message.chat.id
        userId = message.from_user.id
        new_book = message.text.replace('/', '')
        new_book = str(userId) + '_' + new_book
        tb.send_chat_action(chatid, 'typing')
        books_list = list(fh.db.get_user_books(userId))
        if new_book in books_list:
            fh.db.update_current_book(userId, chatid, new_book)
            tb.send_message(chatid, 'Now you read {0}. /more'.format(
                new_book),
                            reply_markup=user_markup_normal)
        else:
            tb.send_message(chatid, config.error_book_recognition)
    except Exception as e:
        tb.reply_to(message, e)


@tb.message_handler(commands=['more'])
def listener(message):
    try:
        chatid = message.chat.id
        userId = message.from_user.id
        tb.send_chat_action(chatid, 'typing')
        tb.send_message(chatid, fh.get_next_portion(userId),
                        reply_markup=remove_markup)
    except Exception as e:
        tb.reply_to(message, e)


@tb.message_handler(commands=['help'])
def help_handler(message):
    try:
        chatid = message.chat.id
        tb.send_chat_action(chatid, 'typing')
        tb.send_message(chatid, config.message_help,
                        reply_markup=user_markup_normal)
    except Exception as e:
        tb.reply_to(message, e)


@tb.message_handler(commands=['sayhi'])
def sayhi_handler(message):
    try:
        chatid = message.chat.id
        tb.send_message(chatid, 'Hi sir!')
    except Exception as e:
        tb.reply_to(message, e)


@tb.message_handler(commands=['now_reading'])
def now_reading_handler(message):
    try:
        chat_id, user_id = message.chat.id, message.from_user.id
        tb.send_chat_action(chat_id, 'typing')
        book_name = fh.db.get_current_book(user_id).replace(
            str(user_id) + '_', '')
        if book_name != -1:
            tb.send_message(chat_id, book_name,
                            reply_markup=user_markup_normal)
        else:
            tb.send_message(chat_id, config.error_current_book,
                            reply_markup=user_markup_normal)
    except Exception as e:
        tb.reply_to(message, e)


@tb.message_handler(commands=['poem_mode'])
def poem_mode_handler(message):
    try:
        chatid = message.chat.id
        userId = message.from_user.id
        poem_mode_userId_list.add(userId)
        tb.send_chat_action(chatid, 'typing')
        tb.send_message(chatid, config.message_poem_mode_ON,
                        reply_markup=remove_markup)
    except Exception as e:
        tb.reply_to(message, e)


# def _get_file_user_sent(message):
#     # get file and filename which have been sent by user in bot
#     file_info = tb.get_file(message.document.file_id)
#     downloaded_file = tb.download_file(file_info.file_path)
#     filename = TextTransliter(message.document.file_name).get_translitet()
#     return downloaded_file, filename


def _get_user_send_mode(user_id):
    user_send_mode = 'by_sense'
    if user_id in poem_mode_userId_list:
        # if user set poem_mode, remember it and delete from query
        user_send_mode = 'by_newline'
        poem_mode_userId_list.remove(user_id)
    return user_send_mode


@tb.message_handler(content_types=['document'])
def handle_document(message):
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id
        path_for_save = config.path_for_save

        file_extractor = FileExtractor()
        file_from_user = file_extractor.local_save_file(tb, message, path_for_save)
        downloaded_file, filename = file_extractor.get_file_user_sent(tb, message)
        # todo make it throw regex, ept
        if (file_from_user != -1):
            # fh.add_new_book(user_id, chat_id, file_from_user, sent_mode=current_user_send_mode)
            book_adder.add_new_book(user_id, chat_id, file_from_user, sent_mode=_get_user_send_mode(user_id))
            tb.send_message(chat_id, config.success_file_added,
                            reply_markup=remove_markup)
        else:
            tb.send_message(chat_id, config.error_file_type)
    except Exception as e:
        logger.error(e)
        tb.reply_to(message, e)


def auto_send_portions():
    send_list = fh.db.get_users_for_autosend()
    for item in send_list:
        try:
            userId = item[0]
            chatId = item[1]
            tb.send_chat_action(chatId, 'typing')
            tb.send_message(chatId, fh.get_next_portion(userId))
        except Exception as e:
            logger.error(e)
    return 0


def save_file(downloaded_file, download_path, filename):
    """"""
    src = os.path.join(download_path, filename)
    with open(src, 'wb') as new_file:
        new_file.write(downloaded_file)
    return src


@tb.message_handler(func=lambda message: True, content_types=['text'])
def command_default(message):
    # this is the standard reply to a normal message
    chat_id, user_id = message.chat.id, message.from_user.id
    tb.send_message(chat_id, config.message_dont_understand.format(message.text))


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
