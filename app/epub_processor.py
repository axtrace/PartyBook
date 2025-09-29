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

    def _send_progress_message(self, bot, chat_id, message):
        """Send progress message to Telegram chat"""
        if bot and chat_id:
            try:
                bot.send_chat_action(chat_id, 'typing')
                bot.send_message(chat_id, message)
            except Exception as e:
                print(f"❌ Ошибка отправки сообщения в Telegram: {e}")

    def process_epub(self, user_id, epub_path, sending_mode='by_sense', bot=None, chat_id=None):
        """
        Process EPUB file and save chunks to database
        
        Args:
            user_id: ID of the user who uploaded the book
            epub_path: Path to the EPUB file
            sending_mode: Mode for text separation ('by_sense' or 'by_newline')
            bot: Telegram bot instance for sending progress messages
            chat_id: Chat ID for sending progress messages
            
        Returns:
            book_id: ID of the created book in database
        """
        try:
            print(f"📖 Начинаем обработку EPUB: {epub_path}")
            
            # Read EPUB file
            book_reader = EpubReader(epub_path)
            book_title = book_reader.get_booktitle()
            print(f"📚 Название книги: {book_title}")
            
            if not book_title:
                raise ValueError("Could not extract book title from EPUB")
            
            # Send initial message
            self._send_progress_message(bot, chat_id, f"📚 Начинаю обработку книги: {book_title}")
            
            # Create filename for database
            book_name = self._make_filename(user_id, book_title)
            print(f"📝 Имя файла для БД: {book_name}")
            
            # Get or create book in database
            print(f"💾 Создаем/получаем книгу в БД...")
            self._send_progress_message(bot, chat_id, "💾 Создаю запись в базе данных...")
            book_id = self.db.get_or_create_book(book_name)
            print(f"✅ Книга создана с ID: {book_id}")
            
            if book_id is None:
                raise ValueError(f"Не удалось создать или найти книгу: {book_name}")
            
            self._send_progress_message(bot, chat_id, f"✅ Книга создана в базе данных (ID: {book_id})")
            
            # Process text and create chunks
            print(f"📄 Начинаем разбивку на чанки...")
            self._send_progress_message(bot, chat_id, "📄 Начинаю разбивку текста на части...")
            
            text_blocks_processed = 0
            total_chunks_created = 0
            empty_blocks_skipped = 0
            
            # Получаем первый блок текста
            print(f"🔄 Получаем первый блок текста...")
            cur_text = book_reader.get_next_item_text()
            print(f"📊 Первый блок получен: {cur_text is not None}, длина: {len(cur_text) if cur_text else 0}")
            
            while cur_text is not None:
                if cur_text.strip():  # Only process non-empty text
                    print(f"🔄 Обрабатываем текст длиной {len(cur_text)} символов...")
                    try:
                        chunks_created = self.chunk_manager.create_chunks(book_id, cur_text, sending_mode)
                        total_chunks_created += chunks_created
                        text_blocks_processed += 1
                        print(f"📊 Обработано блоков: {text_blocks_processed}, создано чанков: {total_chunks_created}")
                        
                        # Отправляем сообщение о прогрессе каждые 5 блоков
                        if text_blocks_processed % 5 == 0:
                            self._send_progress_message(bot, chat_id, 
                                f"📊 Обработано блоков: {text_blocks_processed}, создано чанков: {total_chunks_created}")
                        
                    except Exception as e:
                        print(f"❌ Ошибка при обработке текстового блока: {e}")
                        # Продолжаем обработку других блоков
                else:
                    empty_blocks_skipped += 1
                    print(f"⚠️ Пропущен пустой блок #{empty_blocks_skipped}")
                
                # Получаем следующий блок текста
                print(f"🔄 Получаем следующий блок текста...")
                cur_text = book_reader.get_next_item_text()
                print(f"📊 Следующий блок получен: {cur_text is not None}, длина: {len(cur_text) if cur_text else 0}")
            
            print(f"✅ Обработка завершена. Обработано блоков: {text_blocks_processed}, создано чанков: {total_chunks_created}, пропущено пустых: {empty_blocks_skipped}")
            
            # Отправляем финальное сообщение
            self._send_progress_message(bot, chat_id, 
                f"✅ Обработка завершена!\n📊 Обработано блоков: {text_blocks_processed}\n📚 Создано чанков: {total_chunks_created}")
            
            return book_id
            
        except Exception as e:
            print(f"❌ Error processing EPUB: {str(e)}")
            import traceback
            print(f"❌ Traceback: {traceback.format_exc()}")
            return None
