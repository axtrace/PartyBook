import os
import errno
from time import gmtime, strftime
from text_separator import TextSeparator
import config
from .db_manager import DbManager

class BookChunkManager(object):
    """
    Class for managing book text chunks in YDB
    """

    def __init__(self):
        self.db = DbManager()
        self.chunk_size = config.piece_size

    def create_chunks(self, book_id, text, sent_mode):
        # Разбиваем текст на предложения
        sentences = TextSeparator(text, mode=sent_mode).get_sentences()
        
        # Группируем предложения в чанки
        current_chunk = ""
        chunk_id = 0
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) > self.chunk_size:
                # Сохраняем текущий чанк
                self.db.save_chunk(book_id, chunk_id, current_chunk)
                chunk_id += 1
                current_chunk = sentence
            else:
                current_chunk += sentence
        
        # Сохраняем последний чанк
        if current_chunk:
            self.db.save_chunk(book_id, chunk_id, current_chunk)

    def read_piece(self, book_id, pos):
        # Получаем чанк из базы данных
        chunk = self.db.get_chunk(book_id, pos)
        if chunk is None:
            return None, pos
        
        return chunk, pos + 1

    def get_total_chunks(self, book_id):
        return self.db.get_total_chunks(book_id)
