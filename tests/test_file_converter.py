import unittest
import os
from file_converter import FileConverter


class TestEpubReader(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_book_3rd_text(self):
        fc = FileConverter('/home/axtrace/PycharmProjects/PartyBook/files/')
        epub_path = os.path.join('/home/axtrace/PycharmProjects/PartyBook/tests/', 'test_brodsky.epub')
        result = fc.save_file_as_txt(1111, epub_path)
        self.assertEqual(result, '1111_sobranie_sochinenij.txt')


if __name__ == '__main__':
    unittest.main()
