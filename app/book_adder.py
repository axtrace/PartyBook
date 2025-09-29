from .epub_processor import EpubProcessor
from .books_library import BooksLibrary
import os


class BookAdder(object):
    """add new book to user's library"""

    def __init__(self):
        self.books_lib = BooksLibrary()
        self.epub_processor = EpubProcessor()

    def add_new_book(self, user_id, chat_id, epub_path, sending_mode):
        """
        Process EPUB file and add to user's library
        
        Args:
            user_id: ID of the user
            chat_id: Chat ID for database updates
            epub_path: Path to the EPUB file
            sending_mode: Mode for text separation ('by_sense' or 'by_newline')
            
        Returns:
            book_id: ID of the created book, or -1 if error
        """
        try:
            # Process EPUB file and create chunks in database
            book_id = self.epub_processor.process_epub(user_id, epub_path, sending_mode)
            
            # Update user's current book
            self.books_lib.update_current_book(user_id, chat_id, book_id)
            
            # Set reading position to 0 (start of book)
            self.books_lib.update_book_pos(user_id, book_id, 0)
            
            # Clean up temporary file
            if os.path.exists(epub_path):
                os.remove(epub_path)
            
            return book_id
            
        except Exception as e:
            print(f"Error adding new book: {str(e)}")
            # Clean up temporary file even if there was an error
            if os.path.exists(epub_path):
                os.remove(epub_path)
            return -1
