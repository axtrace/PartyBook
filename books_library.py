from database import *


class BooksLibrary(object):
    """class for manage user books and auto status"""

    def __init__(self):
        self.db = DataBase()

    def update_current_book(self, user_id, chat_id, book_name):
        self.db.update_current_book(user_id, chat_id, book_name)
        pass

    def update_book_pos(self, user_id, current_book, new_pos):
        self.db.update_book_pos(user_id, current_book, new_pos)
        pass

    def switch_auto_staus(self, user_id):
        self.db.update_auto_status(user_id)
        pass

    def get_pos(self, user_id, book_name):
        return self.db.get_pos(user_id, book_name)

    def get_user_books(self, user_id):
        return self.db.get_user_books(user_id)

    def get_auto_status(self, user_id):
        auto_status = self.db.get_auto_status(user_id)
        if auto_status is None:
            return -1
        return auto_status

    def get_users_for_autosend(self):
        return self.db.get_users_for_autosend

    def get_current_book(self, user_id, format_name=False):
        current_book = self.db.get_current_book(user_id)
        if current_book is None:
            return -1
        if format_name:
            current_book = self._format_name(current_book, user_id)
        return current_book

    def _format_name(self, file_name, user_id):
        # Just del user_id and .txt from file_name
        formatted_name = file_name
        formatted_name = formatted_name.replace(str(user_id) + '_', '')
        formatted_name = formatted_name.replace('.txt', '')
        formatted_name = formatted_name.capitalize()
        return formatted_name
