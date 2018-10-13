import os
import errno
import logging
import ebooklib

from ebooklib import epub
from bs4 import BeautifulSoup as bs

import config
import database
from dir_creator import *
from text_separator import TextSeparator
from text_transliter import TextTransliter
from file_converter import FileConverter
from book_adder import *
from file_converter import *


class BookReader():
    """Getting text from book and getting books """

    def __init__(self):

        # logging.basicConfig(filename="sample.log", filemode="w",
        #                    level=logging.ERROR)
        # logger = logging.getLogger("ex")
        self.db = database.DataBase()
        # file_convertor = FileConverter()
        # book_adder = BookAdder()
        # DirCreator(config.path_for_save)

    def get_next_portion(self, user_id):
        # Return next part of text of the book on filename
        # Do not recognise end of file. Return '/more' in the end of message
        current_book = self.db.get_current_book(user_id)
        if current_book == -1:
            return config.error_user_finding  # 'Sorry, did not find you in users.
        pos = self.db.get_pos(user_id, current_book)
        txt_file = open(os.path.join(config.path_for_save, current_book), 'r')
        part = ''
        i = 0
        for i, line in enumerate(txt_file):
            if i >= pos:
                part += line
            if len(part) > config.peaceSize:
                break
        part += '/more'
        txt_file.close()
        self.db.update_book_pos(user_id, current_book, i + 1)
        return part

    # def add_new_book(self, user_id, chatId, epub_path, sent_mode):
#     # convert epub to txt, add to database and delete source epub
#     # bookName = self.put_epub_to_txt(userId, epubPath, sent_mode=sent_mode)
#     book_name = self.file_convertor.save_file_as_txt(user_id, epub_path, sent_mode=sent_mode)
#     self.db.update_current_book(user_id, chatId, book_name)
#     self.db.update_book_pos(user_id, book_name, 0)
#     # have no problem with space on HDD yet. So off this option
#     # os.remove(epubPath)
#     return 0
