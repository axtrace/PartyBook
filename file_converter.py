
import ebooklib
import os

from ebooklib import epub
from bs4 import BeautifulSoup as bs

import config
import db_manager
from text_transliter import TextTransliter
from txt_file import TxtFile
from epub_reader import EpubReader


class FileConverter(object):
    """convert file from epub to txt"""

    def __init__(self, path_for_save=''):
        # db = database.DataBase()
        self.transliter = TextTransliter()
        self.txt_adapter = TxtFile()
        if path_for_save != '':
            self._path_for_save = path_for_save
        else:
            self._path_for_save = config.path_for_save
        pass

    def _make_filename(self, user_id='', book_title=''):
        trans_title = self.transliter.translite_text(book_title)
        trans_title = trans_title.replace(" ", "_").lower()
        filename = str(user_id) + '_' + trans_title
        return filename

    def save_file_as_txt(self, user_id, epub_path, sent_mode='by_sense'):
        # put text of book from epub in new txt file.
        # Return txt file name
        book_reader = EpubReader(epub_path)
        txt_title = self._make_filename(user_id, book_reader.get_booktitle())
        txt_file = TxtFile()
        txt_file.create_file(self._path_for_save, txt_title)

        cur_text = book_reader.get_next_item_text()
        while cur_text is not None:
            txt_file.write_text(cur_text, sent_mode)
            cur_text = book_reader.get_next_item_text()
        txt_file.stop_writing()
        return txt_file.get_filename()
