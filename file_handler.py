import os
import errno
import logging
import ebooklib

from ebooklib import epub
from bs4 import BeautifulSoup as bs

import config
import db_handler
from text_separator import TextSeparator
from text_transliter import TextTransliter
from file_converter import FileConverter


class FileHandler():
    db = db_handler.DBHandler()
    logging.basicConfig(filename="sample.log", filemode="w",
                        level=logging.ERROR)
    logger = logging.getLogger("ex")

    def __init__(self):
        try:
            os.makedirs(config.path_for_save)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

    def get_next_portioin(self, userId):
        # Return next part of text of the book on filename
        # Do not recognise end of file. Return '/more' in the end of message
        curBook = self.db.get_current_book(userId)
        if curBook == -1:
            return config.no_user_found_error  # 'Sorry, did not find you in users.
        pos = self.db.get_pos(userId, curBook)
        txt_file = open(os.path.join(config.path_for_save, curBook),
                        'r')
        part = ''
        i = 0
        for i, line in enumerate(txt_file):
            if i >= pos:
                part += line
            if len(part) > config.peaceSize:
                break
        part += '/more'
        txt_file.close()
        self.db.update_book_pos(userId, curBook, i + 1)
        return part

    def add_new_book(self, userId, chatId, epubPath, sent_mode):
        # convert epub to txt, add to database and delete source epub
        bookName = self.put_epub_to_txt(userId, epubPath, sent_mode=sent_mode)
        self.db.update_current_book(userId, chatId, bookName)
        self.db.update_book_pos(userId, bookName, 0)
        # have no problem with space on HDD yet. So off this option
        # os.remove(epubPath)
        return 0
