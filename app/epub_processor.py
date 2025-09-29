import os
from epub_reader import EpubReader
from txt_file import BookChunkManager
from db_manager import DbManager
from text_transliter import TextTransliter


class EpubProcessor(object):
    """Process EPUB files and convert them to chunks in YDB"""

    def __init__(self):
        self.chunk_manager = BookChunkManager()
        self.db = DbManager()
        self.transliter = TextTransliter()

    def _make_filename(self, user_id, book_title):
        """Create filename for book based on user_id and title"""
        trans_title = self.transliter.translite_text(book_title)
        trans_title = trans_title.replace(" ", "_").lower()
        filename = str(user_id) + '_' + trans_title
        return filename

    def process_epub(self, user_id, epub_path, sending_mode='by_sense'):
        """
        Process EPUB file and save chunks to database
        
        Args:
            user_id: ID of the user who uploaded the book
            epub_path: Path to the EPUB file
            sending_mode: Mode for text separation ('by_sense' or 'by_newline')
            
        Returns:
            book_id: ID of the created book in database
        """
        try:
            # Read EPUB file
            book_reader = EpubReader(epub_path)
            book_title = book_reader.get_booktitle()
            
            if not book_title:
                raise ValueError("Could not extract book title from EPUB")
            
            # Create filename for database
            book_name = self._make_filename(user_id, book_title)
            
            # Get or create book in database
            book_id = self.db.get_or_create_book(book_name)
            
            # Process text and create chunks
            cur_text = book_reader.get_next_item_text()
            while cur_text is not None:
                if cur_text.strip():  # Only process non-empty text
                    self.chunk_manager.create_chunks(book_id, cur_text, sending_mode)
                cur_text = book_reader.get_next_item_text()
            
            return book_id
            
        except Exception as e:
            print(f"Error processing EPUB: {str(e)}")
            raise e
