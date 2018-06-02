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


class TxtFile(object):
    _txt_file = ''
    _txt_file_name = ''

    def __init__(self, userId='', book_title=''):
        self._make_filename_(userId, book_title)
        self._open_file()

    def _open_file(self):
        self._txt_file = open(os.path.join(self.path_for_save, self._txt_file_name), 'w')

    def _close_file(self):
        self._txt_file.close()

    def _make_filename_(self, userId='', book_title=''):
        trans_title = TextTransliter(book_title).get_translitet()
        trans_title = trans_title.replace(" ", "_").lower()
        self._txt_file_name = str(userId) + '_' + trans_title + '.txt'

    def write_text(self, text, sent_mode):
        sentenses = TextSeparator(text, mode=sent_mode).get_sentenses()
        for sent in sentenses:
            print(sent, file=self._txt_file)

    def stop_writing(self):
        print('---THE END---', file=self._txt_file)
        self._close_file()

    def get_file(self):
        return self._txt_file

    def get_file_name(self):
        return self._txt_file_name
