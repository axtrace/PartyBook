class FileManager(object):
    def __init__(self, folder_for_save):
        self.writer = FileWriter(folder_for_save)
        self.reader = FileReader()

    def create_and_write_file(self, text, sent_mode, book_title=''):
        self.writer.create_file(book_title)
        self.writer.write_text(text, sent_mode)
        self.writer.stop_writing()

    def read_piece_from_file(self, file_path, pos, piece_size):
        return self.reader.read_piece(file_path, pos, piece_size)

    def get_filename(self):
        return self.writer.file_name