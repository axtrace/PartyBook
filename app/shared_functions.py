#!/usr/bin/env python3
"""
Общие функции для работы с книгами и отправки сообщений
"""

import config
from books_library import BooksLibrary
from book_reader import BookReader


def book_finished(portion):
    """Проверяет, закончена ли книга"""
    if config.end_book_string in portion:
        return True
    if portion == '/more':
        return True
    return False


def turn_off_autostatus(user_id, chat_id, bot):
    """Отключает автопересылку при завершении книги"""
    books_lib = BooksLibrary()
    if books_lib.get_auto_status(user_id):
        books_lib.switch_auto_status(user_id)
        lang = books_lib.get_lang(user_id)
        if lang not in config.message_everyday_OFF:
            lang = 'ru'  # Fallback на русский язык
        auto_off_msg = config.message_everyday_OFF[lang]
        from telebot.types import ReplyKeyboardMarkup
        user_markup = ReplyKeyboardMarkup(True, one_time_keyboard=True)
        user_markup.row('/start_auto', '/my_books')
        bot.send_message(chat_id, auto_off_msg, reply_markup=user_markup)


def send_portion(user_id, chat_id, bot=None):
    """
    Отправляет следующий чанк пользователю
    Если bot=None, то отправляет через requests (для автопересылки)
    """
    books_lib = BooksLibrary()
    book_reader = BookReader()
    
    try:
        if bot:
            bot.send_chat_action(chat_id, 'typing')
        
        lang = books_lib.get_lang(user_id)
        if lang not in config.error_user_finding:
            lang = 'ru'  # Fallback на русский язык
        
        msg = book_reader.get_next_portion(user_id)
        
        if msg is None:
            msg = config.error_user_finding[lang]
            if bot:
                bot.send_message(chat_id, msg)
            else:
                # Для автопересылки через requests
                return {'success': False, 'reason': 'no_active_book', 'message': msg}
            return -1
            
        if book_finished(msg):
            finished_text = config.message_book_finished[lang]
            msg += f"\n{finished_text}\n/start_auto\n/my_books"
            if bot:
                turn_off_autostatus(user_id, chat_id, bot)
            else:
                # Для автопересылки - отключаем через DbManager
                from db_manager import DbManager
                db = DbManager()
                db.update_auto_status(user_id, False)
                print(f"📚 Книга пользователя {user_id} закончена, автопересылка отключена")
        else:
            msg += '\n/more'
            
        # Отправляем сообщение
        if bot:
            # Обычная отправка через bot
            max_telegram_size = 4096
            for i in range(0, len(msg), max_telegram_size):
                bot.send_message(chat_id, msg[i:i+max_telegram_size])
        else:
            # Для автопересылки возвращаем данные для отправки через requests
            return {'success': True, 'message': msg}
            
        return 0
    except Exception as e:
        if bot:
            bot.send_message(chat_id, f"Error: {str(e)}")
        else:
            return {'success': False, 'error': str(e)}
        return -1
