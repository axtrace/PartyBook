from epub_processor import EpubProcessor
from async_epub_processor import AsyncEpubProcessor
from queue_sender import QueueSender
from books_library import BooksLibrary
from db_manager import DbManager
import os


class BookAdder(object):
    """add new book to user's library"""

    def __init__(self):
        self.books_lib = BooksLibrary()
        self.epub_processor = EpubProcessor()
        self.async_epub_processor = AsyncEpubProcessor()
        self.queue_sender = QueueSender()
        self.db = DbManager()

    def add_new_book(self, user_id, chat_id, epub_path, sending_mode, bot=None):
        """
        Add new book to processing queue for asynchronous processing
        
        Args:
            user_id: ID of the user
            chat_id: Chat ID for database updates
            epub_path: Path to the EPUB file
            sending_mode: Mode for text separation ('by_sense' or 'by_newline')
            bot: Telegram bot instance for sending progress messages
            
        Returns:
            book_id: ID of the created book, or -1 if error
        """
        try:
            print(f"🚀 Начинаем добавление книги для пользователя {user_id}")
            
            # Получаем токен бота для уведомлений
            token = os.environ.get('TOKEN')
            if not token:
                print(f"❌ Токен бота не найден в переменных окружения")
                return -1
            
            # Сохраняем файл в S3 для асинхронной обработки
            print(f"📤 Сохраняем файл в S3 для асинхронной обработки...")
            s3_path = self._upload_to_s3(epub_path, user_id)
            if not s3_path:
                print(f"❌ Ошибка загрузки файла в S3")
                return -1
            
            # Отправляем сообщение в очередь для асинхронной обработки
            print(f"📤 Отправляем книгу в очередь для обработки...")
            success = self.queue_sender.send_book_processing_message(
                user_id, chat_id, s3_path, sending_mode, token
            )
            
            if not success:
                print(f"❌ Ошибка отправки в очередь")
                return -1
            
            # Создаем временную запись о книге для отслеживания
            from epub_reader import EpubReader
            book_reader = EpubReader(epub_path)
            book_title = book_reader.get_booktitle()
            
            if book_title:
                book_name = self._make_filename(user_id, book_title)
                book_id = self.db.get_or_create_book(book_name)
                
                if book_id:
                    print(f"✅ Книга поставлена в очередь обработки, ID: {book_id}")
                    return book_id
            
            print(f"✅ Книга поставлена в очередь обработки")
            return 1  # Возвращаем положительное значение для успеха
            
        except Exception as e:
            print(f"Error adding new book to queue: {str(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return -1

    def _upload_to_s3(self, epub_path, user_id):
        """Upload EPUB file to S3 for asynchronous processing"""
        try:
            import s3_adapter
            s3a = s3_adapter.s3Adapter()
            
            # Создаем уникальное имя файла
            import uuid
            file_id = str(uuid.uuid4())
            s3_key = f"books/{user_id}/{file_id}.epub"
            
            # Загружаем файл в S3
            success = s3a.upload_file(epub_path, s3_key)
            if success:
                print(f"✅ Файл загружен в S3: {s3_key}")
                return s3_key
            else:
                print(f"❌ Ошибка загрузки файла в S3")
                return None
                
        except Exception as e:
            print(f"❌ Ошибка при загрузке файла в S3: {e}")
            return None

    def _make_filename(self, user_id, book_title):
        """Create filename for book based on user_id and title"""
        from text_transliter import TextTransliter
        transliter = TextTransliter()
        trans_title = transliter.translite_text(book_title)
        trans_title = trans_title.replace(" ", "_").lower()
        filename = str(user_id) + '_' + trans_title
        return filename

