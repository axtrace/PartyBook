import os
import database
import config
from books_library import *
from txt_file import *


class BookReader():
    """Getting text from book and getting books """

    def __init__(self):
        self.db = database.DataBase()
        self.books_lib = BooksLibrary()

    def get_next_portion(self, user_id):
        # Return next part of text of the book on filename
        # Do not recognise end of file. Return '/more' in the end of message
        current_book = self.books_lib.get_current_book(user_id)
        if current_book == -1:
            return config.error_user_finding  # 'Sorry, did not find you in users.
        pos = self.books_lib.get_pos(user_id, current_book)
        file_path = os.path.join(config.path_for_save, current_book)
        txt_file = TxtFile()
        text_piece, i = txt_file.read_piece(file_path, pos, config.piece_size)
        # txt_file = open(os.path.join(config.path_for_save, current_book), 'r', encoding='utf-8')
        # part = ''
        # i = 0
        # for i, line in enumerate(txt_file):
        #     if i >= pos:
        #         part += line
        #     if len(part) > config.piece_size:
        #         break
        # part += '/more'
        # txt_file.close()
        self.books_lib.update_book_pos(user_id, current_book, i + 1)
        return text_piece