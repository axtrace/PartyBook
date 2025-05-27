class FileReader:
    def read_piece(self, file_path, pos, piece_size):
        with open(file_path, 'r', encoding='utf-8') as file:
            piece = ''
            for i, line in enumerate(file):
                if i >= pos:
                    piece += line
                if len(piece) > piece_size:
                    break
        return piece, i