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

    def _download_from_s3(self, s3_path, user_id):
        """Download EPUB file from S3 for processing"""
        try:
            import s3_adapter
            s3a = s3_adapter.s3Adapter()
            
            # Создаем локальный путь для файла
            import os
            local_path = f"/tmp/{user_id}_{os.path.basename(s3_path)}"
            
            # Загружаем файл из S3
            success = s3a.download_file(s3_path, local_path)
            if success:
                print(f"✅ Файл загружен из S3: {s3_path} -> {local_path}")
                return local_path
            else:
                print(f"❌ Ошибка загрузки файла из S3: {s3_path}")
                return None
                
        except Exception as e:
            print(f"❌ Ошибка при загрузке файла из S3: {e}")
            return None

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
            # Декодируем сообщение из Yandex Message Queue
            if 'details' in message and 'message' in message['details'] and 'body' in message['details']['message']:
                message_data = json.loads(message['details']['message']['body'])
            elif 'data' in message:
                # Fallback для других форматов
                message_data = json.loads(message['data'])
            else:
                print(f"❌ Нет данных в сообщении: {message}")
                return
            
            print(f"📨 Обрабатываем сообщение: {message_data}")
            
            # Извлекаем данные
            user_id = message_data.get('user_id')
            chat_id = message_data.get('chat_id')
            s3_path = message_data.get('epub_path')  # Теперь это путь в S3
            sending_mode = message_data.get('sending_mode', 'by_sense')
            token = message_data.get('token')
            timestamp = message_data.get('timestamp')
            
            if not all([user_id, chat_id, s3_path, token]):
                print(f"❌ Неполные данные в сообщении: {message_data}")
                return
            
            # Проверяем, не обрабатывается ли уже эта книга
            # Создаем уникальный ключ для проверки дублирования
            processing_key = f"processing_{user_id}_{s3_path}"
            
            # Проверяем, есть ли активная обработка этой книги
            # (это простая проверка, в реальном проекте лучше использовать Redis или БД)
            if hasattr(self, '_active_processing') and processing_key in self._active_processing:
                print(f"⚠️ Книга уже обрабатывается: {processing_key}")
                return
            
            # Отмечаем, что начинаем обработку
            if not hasattr(self, '_active_processing'):
                self._active_processing = set()
            self._active_processing.add(processing_key)
            
            # Загружаем файл из S3
            self._send_telegram_notification(
                chat_id, 
                f"📥 Загружаю файл из облачного хранилища...", 
                token
            )
            
            epub_path = self._download_from_s3(s3_path, user_id)
            if not epub_path:
                print(f"❌ Ошибка загрузки файла из S3: {s3_path}")
                self._send_telegram_notification(
                    chat_id,
                    f"❌ Ошибка загрузки файла из облачного хранилища",
                    token
                )
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
                # Финальное сообщение уже отправлено в _process_epub_completely
                print(f"✅ Обработка книги завершена успешно")
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
            
            # Убираем флаг активной обработки
            if hasattr(self, '_active_processing') and processing_key in self._active_processing:
                self._active_processing.remove(processing_key)
                print(f"✅ Обработка завершена, флаг удален: {processing_key}")
                
        except Exception as e:
            print(f"❌ Ошибка обработки сообщения: {e}")
            import traceback
            print(f"❌ Traceback: {traceback.format_exc()}")
            
            # Убираем флаг активной обработки даже в случае ошибки
            if hasattr(self, '_active_processing') and processing_key in self._active_processing:
                self._active_processing.remove(processing_key)
                print(f"⚠️ Обработка прервана с ошибкой, флаг удален: {processing_key}")

    def _process_epub_completely(self, user_id, chat_id, epub_path, sending_mode, token):
        """
        Полная обработка EPUB файла без ограничений по времени
        """
        try:
            print(f"📖 Начинаем полную обработку EPUB: {epub_path}")
            
            # Читаем EPUB файл
            self._send_telegram_notification(
                chat_id,
                f"📖 Читаю структуру EPUB файла...",
                token
            )
            
            book_reader = EpubReader(epub_path)
            book_title = book_reader.get_booktitle()
            print(f"📚 Название книги: {book_title}")
            
            if not book_title:
                self._send_telegram_notification(
                    chat_id,
                    f"❌ Не удалось извлечь название книги из EPUB файла",
                    token
                )
                return {'success': False, 'error': 'Could not extract book title from EPUB'}
            
            # Создаем книгу в БД
            self._send_telegram_notification(
                chat_id,
                f"💾 Создаю запись в базе данных...",
                token
            )
            
            book_name = self._make_filename(user_id, book_title)
            book_id = self.db.get_or_create_book(book_name)
            
            if book_id is None:
                self._send_telegram_notification(
                    chat_id,
                    f"❌ Ошибка создания записи в базе данных",
                    token
                )
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
                f"📚 Книга: {book_title}\n📊 Найдено {total_items} элементов для обработки\n🔄 Начинаю разбивку на чанки...",
                token
            )
            
            # Обрабатываем все элементы с защитой от бесконечного цикла
            max_processing_attempts = total_items * 2  # Максимум в 2 раза больше элементов
            processing_attempts = 0
            
            # Отправляем сообщение о начале обработки блоков
            self._send_telegram_notification(
                chat_id,
                f"🔄 Начинаю обработку текстовых блоков...\n⏱️ Это может занять несколько минут",
                token
            )
            
            while processing_attempts < max_processing_attempts:
                processing_attempts += 1
                text = book_reader.get_next_item_text()
                if text is None:
                    break
                
                if text.strip():
                    print(f"🔄 Обрабатываем текст длиной {len(text)} символов...")
                    try:
                        chunks_created = self.chunk_manager.create_chunks(book_id, text, sending_mode)
                        total_chunks_created += chunks_created
                        text_blocks_processed += 1
                        
                        # Отправляем прогресс каждые 2 блока для более частых обновлений
                        if text_blocks_processed % 2 == 0:
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
            
            if processing_attempts >= max_processing_attempts:
                print(f"⚠️ Достигнуто максимальное количество попыток обработки ({max_processing_attempts}), прекращаем")
                self._send_telegram_notification(
                    chat_id,
                    f"⚠️ Обработка прервана из-за превышения лимита попыток\n📊 Обработано блоков: {text_blocks_processed}, создано чанков: {total_chunks_created}",
                    token
                )
            
            print(f"✅ Обработка завершена. Обработано блоков: {text_blocks_processed}, создано чанков: {total_chunks_created}, пропущено пустых: {empty_blocks_skipped}")
            
            # Отправляем сообщение о завершении обработки блоков
            self._send_telegram_notification(
                chat_id,
                f"✅ Обработка текста завершена!\n📊 Обработано блоков: {text_blocks_processed}\n📚 Создано чанков: {total_chunks_created}\n🔄 Сохраняю в библиотеку...",
                token
            )
            
            # Обновляем библиотеку пользователя
            from books_library import BooksLibrary
            books_lib = BooksLibrary()
            books_lib.update_current_book(user_id, chat_id, book_id)
            books_lib.update_book_pos(user_id, book_id, 0)
            
            # Отправляем сообщение о завершении сохранения
            self._send_telegram_notification(
                chat_id,
                f"💾 Книга сохранена в вашу библиотеку!\n📖 Теперь вы можете читать книгу командой /more",
                token
            )
            
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

