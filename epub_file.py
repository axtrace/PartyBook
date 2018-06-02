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


class EpubFileReader(object):
    _book = ''
    _txt_file_name = ''
    _items_list = []
    _cur_item_num = 0

    def __init__(self, epub_path):
        self._book = epub.read_epub(epub_path)
        for itemDoc in self._book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            self._items_list.append(itemDoc)

    def get_booktitle(self):
        return self._book.title

    def get_next_item_text(self):
        cur_itemDoc = self._items_list[self._cur_item_num]
        soup = bs(cur_itemDoc.content.decode('utf-8'), "lxml")
        return soup.body.get_text()


if __name__ == '__main__':
    epub_path = os.path.join('/home/axtrace/PycharmProjects/PartyBook/files/brodsky.epub','')
    efr = EpubFileReader(epub_path)
    print(efr.get_booktitle())
