from file_converter import FileConverter
from db_handler import DBHandler


class BookAdder(object):
    # add new book to user's library
    db = DBHandler()

    def init(self):
        pass

    def add_new_book(self, userId, chatId, epub_path, sent_mode):
        # convert epub to txt, add to database and delete source epub
        file_converter = FileConverter()
        book_name = file_converter.save_file_as_txt(userId, epub_path, sent_mode)
        self.db.update_current_book(userId, chatId, book_name)
        self.db.update_book_pos(userId, book_name, 0)
        # have no problem with space on HDD yet. So off this option
        # os.remove(epubPath)
        return 0
