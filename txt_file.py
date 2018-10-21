import os
import errno
from time import gmtime, strftime
from text_separator import TextSeparator

import config


class TxtFile(object):
    """Class for write text in .txt file by sentences"""

    def __init__(self):
        self._txt_file = ''
        self._txt_file_name = ''
        pass

    def create_file(self, folder_for_save, book_title=''):
        try:
            if book_title == '':
                self._txt_file_name = str(
                    strftime("%Y-%m-%d_%H:%M:%S", gmtime())) + '.txt'
            else:
                self._txt_file_name = book_title + '.txt'
            file_path = os.path.join(folder_for_save, self._txt_file_name)
            self._open_file(file_path, mode='w')
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise
        pass

    def _open_file(self, file_path, mode):
        self._txt_file = open(file_path, mode, encoding='utf-8')
        pass

    def _close_file(self):
        self._txt_file.close()
        pass

    def write_text(self, text, sent_mode):
        sentences = TextSeparator(text, mode=sent_mode).get_sentences()
        for sent in sentences:
            print(sent, file=self._txt_file)
        pass

    def stop_writing(self):
        print(config.end_book_string, file=self._txt_file)
        self._close_file()
        pass

    def read_piece(self, file_path, pos, piece_size):
        # txt_file = open(os.path.join(config.path_for_save, current_book), 'r', encoding='utf-8')
        self._open_file(file_path, mode='r')
        piece = ''
        i = 0
        for i, line in enumerate(self._txt_file):
            if i >= pos:
                piece += line
            if len(piece) > piece_size:
                break
        # piece += '/more'
        self._close_file()
        return piece, i

    def get_txt_file(self):
        return self._txt_file

    def get_filename(self):
        return self._txt_file_name
