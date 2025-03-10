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
            self.spine_ids = self._get_spine_ids()
            self.item_ids = self._get_item_ids()
            self.item_ids.sort(key=self._sort_by_spine) # sort list of docs ids in order they follow in spine_ids
        else:
            self.book = None
        pass

    def _get_item_ids(self):
        item_ids = []
        doc_item_list = self.book.get_items_of_type(ebooklib.ITEM_DOCUMENT)
        for elem in doc_item_list:
            item_ids.append(elem.id)
        return item_ids

    def _get_spine_ids(self):
        spine_ids = []
        for sp in self.book.spine:
            spine_ids.append(sp[0])
        return spine_ids

    def get_booktitle(self):
        if self.book is None:
            return ''
        return self.book.title

    def get_toc(self):
        # return table of content
        if self.book is None:
            return ''
        return self.book.toc

    def _sort_by_spine(self, item):
        # for sorting list of items by list of ids from spine.
        # epub readers read book in spine order
        if item not in self.spine_ids:
            return 0
        return self.spine_ids.index(item)

    def get_next_item_text(self):
        # return text of next item with type ITEM_DOCUMENT
        if len(self.item_ids) == 0:
            return None
        item_id = self.item_ids.pop(0)
        item_doc = self.book.get_item_with_id(item_id)
        soup = bs(item_doc.content.decode('utf-8'), "lxml")
        return soup.body.get_text()
