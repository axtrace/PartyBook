import os
import config
from books_library import *
from txt_file import BookChunkManager


class BookReader():
    """
    Getting text from book, moving position.
    Getting books of user
    """

    def __init__(self):
        # self.db = database.DataBase()
        self.books_lib = BooksLibrary()
        self.chunk_manager = BookChunkManager()

    def get_next_portion(self, user_id):
        try:
            # Получаем информацию о текущей книге пользователя
            book_id, book_name, pos, mode = self.books_lib.get_current_book(user_id)
            if book_name == -1: 
                return None

            # Получаем следующий чанк текста
            text_piece, new_pos = self.chunk_manager.read_piece(book_id, pos)
            
            # Если чанк не найден, проверяем, не закончилась ли книга
            if text_piece is None:
                total_chunks = self.chunk_manager.get_total_chunks(book_id)
                if pos >= total_chunks:
                    return config.end_book_string
                return None

            # Если чанк найден, обновляем позицию в книге
            self.books_lib.update_book_pos(user_id, book_id, new_pos)
            return text_piece
        except Exception as e:
            print(f"Error in get_next_portion: {str(e)}")
            return None
