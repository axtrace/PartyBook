from ebooklib import epub
import ebooklib
from bs4 import BeautifulSoup as bs
import os
import logging
from transliterate import translit
import errno
import config
import db_handler
import re
from nltk.tokenize import sent_tokenize


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

    def transliterate(self, s):
        # convert from russian to translit
        return translit(s, "ru", reversed=True).replace(" ",
                                                        "_").lower()

    def get_sentences(self, text):
        def dashrepl(matchobj):
            # function for replace \n + big letter after to '. '
            textpeace = matchobj.group(0)
            return re.sub(r'[\n\r\f\v]+', '. ', textpeace, flags=re.M)

        # replace [letter or digit] + newline + big letter after --> '. '
        spec_regex = r'\w[\n\r\f\v]+[0-9A-ZА-Я]'
        text = re.sub(spec_regex, dashrepl, text, flags=re.M)
        # make one big string from all textlines
        text = re.sub(r'\s+', ' ', text, flags=re.M)
        return sent_tokenize(text, 'russian')

    def put_epub_to_txt(self, userId, EpubPath):
        # put text of book from epub in new txt file. Return txt file name
        book = epub.read_epub(EpubPath)
        txt_file_name = str(userId) + '_' + self.transliterate(
            str(book.title)) + '.txt'
        txt_file = open(
            os.path.join(config.path_for_save, txt_file_name), 'w')

        for itemDoc in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            # get text from book
            soup = bs(itemDoc.content.decode('utf-8'), "lxml")
            text = soup.body.get_text()
            # write to .txt: 1 sentence = 1 line
            for sent in self.get_sentences(text):
                print(sent, file=txt_file)
        print('---THE END---', file=txt_file)
        txt_file.close()
        return txt_file_name

    def get_next_portioin(self, userId):
        # Return next part of text of the book on filename
        # Do not recognise end of file. Return '/more' in the end of message
        curBook = self.db.get_current_book(userId)
        if curBook == -1:
            return config.noUserFoundErr  # 'Sorry, did not find you in users.
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

    def add_new_book(self, userId, chatId, epubPath):
        # convert epub to txt, add to database and delete source epub
        bookName = self.put_epub_to_txt(userId, epubPath)
        self.db.update_current_book(userId, chatId, bookName)
        self.db.update_book_pos(userId, bookName, 0)
        os.remove(epubPath)
        return 0
