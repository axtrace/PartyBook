import os
from text_separator import TextSeparator


class TxtFile(object):
    """Class for write text in .txt file by sentenses"""

    def __init__(self, path_for_save, book_title=''):
        self._txt_file = ''
        self._txt_file_name = ''
        if book_title == '':
            self._txt_file_name = str(os.utime()) + '.txt'
        else:
            self._txt_file_name = book_title + '.txt'
        self._open_file(path_for_save)

    def _open_file(self, path_for_save):
        self._txt_file = open(os.path.join(path_for_save, self._txt_file_name), 'w', encoding='utf-8')

    def _close_file(self):
        self._txt_file.close()

    def write_text(self, text, sent_mode):
        sentenses = TextSeparator(text, mode=sent_mode).get_sentenses()
        for sent in sentenses:
            print(sent, file=self._txt_file)

    def stop_writing(self):
        print('---THE END---', file=self._txt_file)
        self._close_file()

    def get_txt_file(self):
        return self._txt_file

    def get_filename(self):
        return self._txt_file_name
