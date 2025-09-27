import sys
import os
from db_manager import DbManager
from text_replacer import TextReplacer

class BooksLibrary(object):
    """
    Class for manage user books and auto status
    Manage cache for lang
    """

    def __init__(self):
        self.db = DbManager()
        self.lang_cache = {}
        self.text_replacer = TextReplacer()

    def update_current_book(self, user_id, chat_id, book_id):
        lang = self.get_lang(user_id)
        self.db.update_current_book(user_id, chat_id, book_id)
        pass

    def update_book_pos(self, user_id, book_id, new_pos):
        self.db.update_book_pos(user_id, book_id, new_pos)
        pass

    def switch_auto_status(self, user_id):
        if self.db.get_auto_status(user_id):
            self.db.update_auto_status(user_id, False)
        else:
            self.db.update_auto_status(user_id, True)
        return 0

    def update_lang(self, user_id, lang):
        self.db.update_user_lang(user_id, lang)
        self.lang_cache[user_id] = lang
        return 0

    def get_pos(self, user_id, book_id):
        return self.db.get_book_pos(user_id, book_id)

    def get_lang(self, user_id):
        lang = self.lang_cache.get(user_id, None)
        if lang is None:
            lang = self.db.get_user_lang(user_id)
            if lang is None:
                lang = 'ru'
                self.update_lang(user_id, lang)
        return lang

    def get_user_books(self, user_id):
        return self.db.get_user_books(user_id)

    def get_auto_status(self, user_id):
        auto_status = self.db.get_auto_status(user_id)
        if auto_status is None:
            return -1
        return auto_status

    def get_users_for_autosend(self):
        return self.db.get_users_for_autosend()

    def get_current_book(self, user_id, is_format_name_needed=False):
        print(f"get_current_book. user_id: {user_id}, is_format_name_needed: {is_format_name_needed}")
        book_id, book_name, pos, mode = self.db.get_current_book(user_id)
        print(f"get_current_book. book_id: {book_id}, book_name: {book_name}, pos: {pos}, mode: {mode}")
        if book_name is None:
            return -1, -1, -1, -1
        if is_format_name_needed:
            book_name = self._format_name(book_name, user_id)
        return book_id, book_name, pos, mode

    def _format_name(self, file_name, user_id):
        # Just del user_id and .txt from file_name
        text_dict = {
                 str(user_id) + '_': '',
                 '.txt': '',
        }

        formatted_name = self.text_replacer.text_replace(file_name, text_dict)
        formatted_name = formatted_name.capitalize()
        return formatted_name
