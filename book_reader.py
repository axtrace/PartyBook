import os
import config
from books_library import *
from txt_file import *


class BookReader():
    """
    Getting text from book, moving position.
    Getting books of user
    """

    def __init__(self):
        # self.db = database.DataBase()
        self.books_lib = BooksLibrary()
        self.txt_file = TxtFile()

    def get_next_portion(self, user_id):
        # Return next text part of the book. Do not recognise end of file.
        # Return '/more' in the end of message
        book_id, file_name, pos = self.books_lib.get_current_book(user_id)
        if file_name == -1:
            return None # 'Sorry, did not find you in users.
        # pos = self.books_lib.get_pos(user_id, file_name)
        # file_path = os.path.join(config.path_for_save, file_name)
        text_piece, i = self.txt_file.read_piece(file_name, pos, config.piece_size)
        self.books_lib.update_book_pos(user_id, file_name, i + 1)
        return text_piece
