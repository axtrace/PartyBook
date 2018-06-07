import logging
import ebooklib
import os

from ebooklib import epub
from bs4 import BeautifulSoup as bs

import config
import db_handler
from text_transliter import TextTransliter
from txt_file import TxtFile
from epub_reader import EpubReader


class FileConverter(object):
    db = db_handler.DBHandler()
    logging.basicConfig(filename="sample.log", filemode="w",
                        level=logging.ERROR)
    logger = logging.getLogger("ex")

    _path_for_save = ''

    def __init__(self, path_for_save=''):
        if path_for_save != '':
            self._path_for_save = path_for_save
        else:
            self._path_for_save = config.path_for_save

    def _make_filename(self, userId='', book_title=''):
        trans_title = TextTransliter(book_title).get_translitet()
        trans_title = trans_title.replace(" ", "_").lower()
        filename = str(userId) + '_' + trans_title
        return filename

    def save_file_as_txt(self, userId, EpubPath, sent_mode='by_sense'):
        # put text of book from epub in new txt file. Return txt file name
        book_reader = EpubReader(EpubPath)
        txt_title = self._make_filename(userId, book_reader.get_booktitle())
        txt_file = TxtFile(self._path_for_save, txt_title)

        cur_text = book_reader.get_next_item_text()
        while cur_text != None:
            txt_file.write_text(cur_text, sent_mode)
            cur_text = book_reader.get_next_item_text()
        txt_file.stop_writing()
        return txt_file.get_file_name()


if __name__ == '__main__':
    fc = FileConverter('/home/axtrace/PycharmProjects/PartyBook/files/')
    epub_path = os.path.join('/home/axtrace/PycharmProjects/PartyBook/tests/', 'test_brodsky.epub')
    txt_file = fc.save_file_as_txt(1111, epub_path)
    print(txt_file)
