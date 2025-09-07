from file_converter import FileConverter
# from db_manager import DatabaseManager
from books_library import *


class BookAdder(object):
    """add new book to user's library"""

    def __init__(self):
        self.books_lib = BooksLibrary()
        # self.db = DatabaseManager()
        self.fc = FileConverter()
        pass

    def add_new_book(self, user_id, chat_id, epub_path, sending_mode):
        # convert epub to txt, add to database and delete source epub
        book_name = self.fc.save_file_as_txt(user_id, epub_path,
                                                    sending_mode)
        self.books_lib.update_current_book(user_id, chat_id, book_name)
        self.books_lib.update_book_pos(user_id, book_name, 0)
        return 0
