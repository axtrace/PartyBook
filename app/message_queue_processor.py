import json
import os
import boto3
from epub_reader import EpubReader
from txt_file import BookChunkManager
from db_manager import DbManager
from text_transliter import TextTransliter


class MessageQueueProcessor(object):
    """Обработчик сообщений из Message Queue для обработки книг"""

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

    def _send_telegram_notification(self, chat_id, message, token):
        """Отправляем уведомление в Telegram"""
        try:
            import requests
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            data = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            response = requests.post(url, data=data)
            if response.status_code == 200:
                print(f"✅ Уведомление отправлено в Telegram: {message}")
            else:
                print(f"❌ Ошибка отправки в Telegram: {response.status_code}")
        except Exception as e:
            print(f"❌ Ошибка отправки уведомления: {e}")

    def process_book_from_queue(self, event, context):
        """
        Главная функция для обработки сообщений из Message Queue
        
        Args:
            event: Событие от Message Queue
            context: Контекст выполнения функции
            
        Returns:
            dict: Результат обработки
        """
        try:
            print(f"🔄 Получено событие от Message Queue: {event}")
            
            # Парсим сообщение из очереди
            if 'messages' in event:
                for message in event['messages']:
                    self._process_single_message(message)
            else:
                print(f"❌ Неожиданный формат события: {event}")
                return {'statusCode': 400, 'body': 'Invalid event format'}
            
            return {'statusCode': 200, 'body': 'Processing completed'}
            
        except Exception as e:
            print(f"❌ Ошибка обработки сообщения: {e}")
            import traceback
            print(f"❌ Traceback: {traceback.format_exc()}")
            return {'statusCode': 500, 'body': f'Error: {str(e)}'}

    def _process_single_message(self, message):
        """Обрабатываем одно сообщение из очереди"""
        try:
            # Декодируем сообщение
            if 'data' in message:
                message_data = json.loads(message['data'])
            else:
                print(f"❌ Нет данных в сообщении: {message}")
                return
            
            print(f"📨 Обрабатываем сообщение: {message_data}")
            
            # Извлекаем данные
            user_id = message_data.get('user_id')
            chat_id = message_data.get('chat_id')
            epub_path = message_data.get('epub_path')
            sending_mode = message_data.get('sending_mode', 'by_sense')
            token = message_data.get('token')
            
            if not all([user_id, chat_id, epub_path, token]):
                print(f"❌ Неполные данные в сообщении: {message_data}")
                return
            
            # Отправляем уведомление о начале обработки
            self._send_telegram_notification(
                chat_id, 
                f"📚 Начинаю обработку книги...\n⏱️ Это займет несколько минут", 
                token
            )
            
            # Обрабатываем книгу
            result = self._process_epub_completely(
                user_id, chat_id, epub_path, sending_mode, token
            )
            
            if result['success']:
                # Уведомляем об успешном завершении
                self._send_telegram_notification(
                    chat_id,
                    f"🎉 Книга успешно обработана!\n📚 Создано чанков: {result['chunks_created']}\n📖 Теперь вы можете читать книгу командой /more",
                    token
                )
            else:
                # Уведомляем об ошибке
                self._send_telegram_notification(
                    chat_id,
                    f"❌ Ошибка обработки книги: {result['error']}",
                    token
                )
            
            # Очищаем временный файл
            if os.path.exists(epub_path):
                os.remove(epub_path)
                print(f"🗑️ Временный файл удален: {epub_path}")
                
        except Exception as e:
            print(f"❌ Ошибка обработки сообщения: {e}")
            import traceback
            print(f"❌ Traceback: {traceback.format_exc()}")

    def _process_epub_completely(self, user_id, chat_id, epub_path, sending_mode, token):
        """
        Полная обработка EPUB файла без ограничений по времени
        """
        try:
            print(f"📖 Начинаем полную обработку EPUB: {epub_path}")
            
            # Читаем EPUB файл
            book_reader = EpubReader(epub_path)
            book_title = book_reader.get_booktitle()
            print(f"📚 Название книги: {book_title}")
            
            if not book_title:
                return {'success': False, 'error': 'Could not extract book title from EPUB'}
            
            # Создаем книгу в БД
            book_name = self._make_filename(user_id, book_title)
            book_id = self.db.get_or_create_book(book_name)
            
            if book_id is None:
                return {'success': False, 'error': f'Could not create book: {book_name}'}
            
            print(f"✅ Книга создана с ID: {book_id}")
            
            # Обрабатываем все элементы книги
            total_chunks_created = 0
            text_blocks_processed = 0
            empty_blocks_skipped = 0
            
            # Получаем общее количество элементов
            total_items = len(book_reader.item_ids)
            print(f"📊 Всего элементов для обработки: {total_items}")
            
            # Отправляем промежуточное уведомление
            self._send_telegram_notification(
                chat_id,
                f"📊 Найдено {total_items} элементов для обработки\n🔄 Начинаю разбивку на чанки...",
                token
            )
            
            # Обрабатываем все элементы
            while True:
                text = book_reader.get_next_item_text()
                if text is None:
                    break
                
                if text.strip():
                    print(f"🔄 Обрабатываем текст длиной {len(text)} символов...")
                    try:
                        chunks_created = self.chunk_manager.create_chunks(book_id, text, sending_mode)
                        total_chunks_created += chunks_created
                        text_blocks_processed += 1
                        
                        # Отправляем прогресс каждые 10 блоков
                        if text_blocks_processed % 10 == 0:
                            progress_percent = (text_blocks_processed / total_items) * 100
                            self._send_telegram_notification(
                                chat_id,
                                f"📊 Прогресс: {text_blocks_processed}/{total_items} ({progress_percent:.1f}%)\n📚 Создано чанков: {total_chunks_created}",
                                token
                            )
                        
                        print(f"📊 Обработано блоков: {text_blocks_processed}, создано чанков: {total_chunks_created}")
                        
                    except Exception as e:
                        print(f"❌ Ошибка при обработке текстового блока: {e}")
                        # Продолжаем обработку других блоков
                else:
                    empty_blocks_skipped += 1
                    print(f"⚠️ Пропущен пустой блок #{empty_blocks_skipped}")
            
            print(f"✅ Обработка завершена. Обработано блоков: {text_blocks_processed}, создано чанков: {total_chunks_created}, пропущено пустых: {empty_blocks_skipped}")
            
            # Обновляем библиотеку пользователя
            from books_library import BooksLibrary
            books_lib = BooksLibrary()
            books_lib.update_current_book(user_id, chat_id, book_id)
            books_lib.update_book_pos(user_id, book_id, 0)
            
            return {
                'success': True,
                'book_id': book_id,
                'chunks_created': total_chunks_created,
                'blocks_processed': text_blocks_processed
            }
            
        except Exception as e:
            print(f"❌ Error processing EPUB completely: {str(e)}")
            import traceback
            print(f"❌ Traceback: {traceback.format_exc()}")
            return {'success': False, 'error': str(e)}

