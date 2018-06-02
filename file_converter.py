import os
import errno
import logging
import ebooklib

from ebooklib import epub
from bs4 import BeautifulSoup as bs

import config
import db_handler
from dir_creator import DirCreator
from text_separator import TextSeparator
from text_transliter import TextTransliter
from txt_file import TxtFile


class FileConverter(object):
    db = db_handler.DBHandler()
    logging.basicConfig(filename="sample.log", filemode="w",
                        level=logging.ERROR)
    logger = logging.getLogger("ex")

    path_for_save = ''

    def __init__(self, path_for_save=''):
        if path_for_save != '':
            self.path_for_save = path_for_save
        else:
            self.path_for_save = config.path_for_save

    def _make_filename(self, userId='', book_title=''):
        trans_title = TextTransliter(book_title).get_translitet()
        trans_title = trans_title.replace(" ", "_").lower()
        filename = str(userId) + '_' + trans_title + '.txt'
        return filename

    def save_file_as_txt(self, userId, EpubPath, sent_mode='by_sense'):
        # put text of book from epub in new txt file. Return txt file name
        book = epub.read_epub(EpubPath)
        txt_file = TxtFile(userId, book.title)

        for itemDoc in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            # get text from part of the book
            soup = bs(itemDoc.content.decode('utf-8'), "lxml")
            text = soup.body.get_text()
            # write to .txt: 1 sentence = 1 line
            txt_file.write_text(text, sent_mode)
        txt_file.stop_writing()
        return txt_file_name
