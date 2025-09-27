import os
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup as bs
import config
from db_manager import DbManager
from text_transliter import TextTransliter
from txt_file import BookChunkManager
from epub_reader import EpubReader

class FileConverter(object):
    """convert file from epub to chunks in YDB"""

    def __init__(self, path_for_save=''):
        self.transliter = TextTransliter()
        self.chunk_manager = BookChunkManager()
        if path_for_save != '':
            self._path_for_save = path_for_save
        else:
            self._path_for_save = config.path_for_save

    def _make_filename(self, user_id='', book_title=''):
        trans_title = self.transliter.translite_text(book_title)
        trans_title = trans_title.replace(" ", "_").lower()
        filename = str(user_id) + '_' + trans_title
        return filename

    def save_file_as_chunks(self, user_id, epub_path, sent_mode='by_sense'):
        # Convert epub to chunks and save in YDB
        book_reader = EpubReader(epub_path)
        book_title = self._make_filename(user_id, book_reader.get_booktitle())
        
        # Получаем ID книги из базы данных
        db = db_manager.DbManager()
        book_id = db.get_or_create_book(book_title)
        
        # Читаем и сохраняем текст по частям
        cur_text = book_reader.get_next_item_text()
        while cur_text is not None:
            self.chunk_manager.create_chunks(book_id, cur_text, sent_mode)
            cur_text = book_reader.get_next_item_text()
            
        return book_id
