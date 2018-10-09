import os
from bs4 import BeautifulSoup as bs
import ebooklib
from ebooklib import epub


class EpubReader():
    # reade text from epub file

    def __init__(self, epub_path=''):
        self.epub_path = epub_path
        if epub_path != '':
            self.book = epub.read_epub(epub_path)
            self.item_list = []
            for item_doc in self.book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
                self.item_list.append(item_doc)
        else:
            self.book = None

    def get_booktitle(self):
        if self.book is None:
            return ''
        return self.book.title

    def get_next_item_text(self):
        # return text of next item with type ITEM_DOCUMENT
        if len(self.item_list) != 0:
            item_doc = self.item_list.pop(0)
            soup = bs(item_doc.content.decode('utf-8'), "lxml")
            return soup.body.get_text()
        return None

    def get_items_of_type(self, type):
        return self.book.get_items_of_type(ebooklib.ITEM_DOCUMENT)


if __name__ == '__main__':
    epub_path = os.path.join(os.getcwd(), '1.epub')
    eb = EpubReader(os.path.normpath(epub_path))
    print(eb.get_booktitle())
    for x in range(40):
        print(eb.get_next_item_text())
