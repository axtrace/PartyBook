import unittest
import os
from epub_reader import EpubReader


class TestEpubReader(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_empty_line(self):
        epub_path = ''
        result = EpubReader(epub_path).get_booktitle()
        self.assertEqual(result, '')

    def test_book_title(self):
        epub_path = os.path.join('/home/axtrace/PycharmProjects/PartyBook/tests/', 'test_brodsky.epub')
        result = EpubReader(epub_path).get_booktitle()
        self.assertEqual(result, 'Собрание сочинений')

    def test_book_3rd_text(self):
        epub_path = os.path.join('/home/axtrace/PycharmProjects/PartyBook/tests/', 'test_brodsky.epub')
        efr = EpubReader(epub_path)
        for i in range(4):
            text = efr.get_next_item_text()
        result = text.split()
        self.assertEqual(result[1], 'Неопубликованные')


if __name__ == '__main__':
    unittest.main()
