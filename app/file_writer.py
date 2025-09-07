import os
import errno
from time import gmtime, strftime
from text_separator import TextSeparator
from s3_adapter import s3Adapter
from nltk.tokenize import sent_tokenize

class FileWriter(object):
    """
    Class for write text in .txt file by sentences
    """

    def __init__(self, folder_for_save):
        self.folder_for_save = folder_for_save
        self.file = None
        self.file_name = ''
        self.s3a = s3Adapter()

    def create_file(self, book_title=''):

        try:
            if book_title == '':
                self._txt_file_name = str(strftime("%Y-%m-%d_%H:%M:%S", gmtime())) + '.txt'
            else:
                self._txt_file_name = book_title + '.txt'
            file_path = os.path.join(self.folder_for_save, self._txt_file_name)
            self._open_file(file_path, mode='w')
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise
        pass


        self.file_name = f"{book_title or strftime('%Y-%m-%d_%H:%M:%S', gmtime())}.txt"
        file_path = os.path.join(self.folder_for_save, self.file_name)
        self.file = open(file_path, 'w', encoding='utf-8')

    def write_text(self, text, sent_mode):
        sentences = TextSeparator(text, mode=sent_mode).get_sentences()
        for sent in sentences:
            print(sent, file=self.file)

    def stop_writing(self):
        print(config.end_book_string, file=self.file)
        self.file.close()