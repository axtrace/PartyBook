#!/usr/bin/env python3
"""
Параллельный процессор книг для Yandex Cloud Functions
Разбивает обработку книги на множество параллельных задач
"""

import json
import os
import uuid
from epub_reader import EpubReader
from db_manager import DbManager
from text_transliter import TextTransliter
from queue_sender import QueueSender


class ParallelBookProcessor(object):
    """Координатор для параллельной обработки книг"""

    def __init__(self):
        self.db = DbManager()
        self.transliter = TextTransliter()
        self.queue_sender = QueueSender()

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
                print(f"✅ Уведомление отправлено: {message}")
            else:
                print(f"❌ Ошибка отправки в Telegram: {response.status_code}")
        except Exception as e:
            print(f"❌ Ошибка отправки уведомления: {e}")

    def start_parallel_processing(self, user_id, chat_id, epub_path, sending_mode, token):
        """
        Начинает параллельную обработку книги
        
        Args:
            user_id: ID пользователя
            chat_id: ID чата для уведомлений
            epub_path: Путь к EPUB файлу
            sending_mode: Режим разбивки текста
            token: Токен бота для уведомлений
            
        Returns:
            dict: Результат инициализации
        """
        try:
            print(f"🚀 Начинаем параллельную обработку книги для пользователя {user_id}")
            
            # Создаем уникальный ID для этой обработки
            processing_id = str(uuid.uuid4())
            print(f"🆔 ID обработки: {processing_id}")
            
            # Читаем EPUB файл
            self._send_telegram_notification(
                chat_id,
                f"📖 Анализирую структуру книги...",
                token
            )
            
            book_reader = EpubReader(epub_path)
            book_title = book_reader.get_booktitle()
            
            if not book_title:
                self._send_telegram_notification(
                    chat_id,
                    f"❌ Не удалось извлечь название книги",
                    token
                )
                return {'success': False, 'error': 'Could not extract book title'}
            
            print(f"📚 Название книги: {book_title}")
            
            # Создаем книгу в БД
            book_name = self._make_filename(user_id, book_title)
            book_id = self.db.get_or_create_book(book_name)
            
            if book_id is None:
                self._send_telegram_notification(
                    chat_id,
                    f"❌ Ошибка создания записи в БД",
                    token
                )
                return {'success': False, 'error': 'Could not create book in DB'}
            
            # Получаем все текстовые блоки
            all_text_blocks = []
            while True:
                text = book_reader.get_next_item_text()
                if text is None:
                    break
                if text.strip():  # Только непустые блоки
                    all_text_blocks.append(text)
            
            total_blocks = len(all_text_blocks)
            print(f"📊 Найдено {total_blocks} текстовых блоков")
            
            if total_blocks == 0:
                self._send_telegram_notification(
                    chat_id,
                    f"❌ В книге не найдено текстового содержимого",
                    token
                )
                return {'success': False, 'error': 'No text content found'}
            
            # Разбиваем на батчи для параллельной обработки
            batch_size = 10  # По 10 блоков на функцию
            batches = []
            for i in range(0, total_blocks, batch_size):
                batch_blocks = all_text_blocks[i:i + batch_size]
                batch_id = f"{processing_id}_batch_{i // batch_size}"
                batches.append({
                    'batch_id': batch_id,
                    'blocks': batch_blocks,
                    'start_index': i,
                    'end_index': min(i + batch_size - 1, total_blocks - 1)
                })
            
            print(f"📦 Создано {len(batches)} батчей для обработки")
            
            # Сохраняем метаданные обработки в БД
            processing_metadata = {
                'processing_id': processing_id,
                'user_id': user_id,
                'chat_id': chat_id,
                'book_id': book_id,
                'book_title': book_title,
                'total_blocks': total_blocks,
                'total_batches': len(batches),
                'completed_batches': 0,
                'sending_mode': sending_mode,
                'token': token,
                'status': 'processing',
                'batches': [batch['batch_id'] for batch in batches]
            }
            
            self._save_processing_metadata(processing_id, processing_metadata)
            
            # Отправляем уведомление о начале обработки
            self._send_telegram_notification(
                chat_id,
                f"📚 <b>{book_title}</b>\n"
                f"📊 Найдено {total_blocks} текстовых блоков\n"
                f"📦 Разбито на {len(batches)} частей для параллельной обработки\n"
                f"⚡ Начинаю обработку...",
                token
            )
            
            # Отправляем батчи в очередь для обработки
            for batch in batches:
                self._send_batch_to_queue(processing_id, batch, book_id, sending_mode, token)
            
            return {
                'success': True,
                'processing_id': processing_id,
                'book_id': book_id,
                'total_batches': len(batches),
                'total_blocks': total_blocks
            }
            
        except Exception as e:
            print(f"❌ Ошибка в параллельной обработке: {e}")
            import traceback
            print(f"❌ Traceback: {traceback.format_exc()}")
            return {'success': False, 'error': str(e)}

    def _save_processing_metadata(self, processing_id, metadata):
        """Сохраняем метаданные обработки в БД"""
        try:
            # Создаем таблицу для метаданных обработки, если её нет
            create_table_query = """
                CREATE TABLE IF NOT EXISTS processing_metadata (
                    processing_id Utf8,
                    metadata Json,
                    created_at Timestamp,
                    PRIMARY KEY (processing_id)
                );
            """
            self.db.db_adapter.execute_query(create_table_query)
            
            # Сохраняем метаданные
            insert_query = f"""
                INSERT INTO processing_metadata (processing_id, metadata, created_at)
                VALUES ('{processing_id}', '{json.dumps(metadata)}', CurrentUtcTimestamp());
            """
            self.db.db_adapter.execute_query(insert_query)
            print(f"💾 Метаданные обработки сохранены: {processing_id}")
            
        except Exception as e:
            print(f"❌ Ошибка сохранения метаданных: {e}")

    def _get_processing_metadata(self, processing_id):
        """Получаем метаданные обработки из БД"""
        try:
            query = f"""
                SELECT metadata FROM processing_metadata
                WHERE processing_id = '{processing_id}';
            """
            result = self.db.db_adapter.execute_query(query)
            if result and len(result[0].rows) > 0:
                metadata_str = str(result[0].rows[0][0])
                return json.loads(metadata_str)
        except Exception as e:
            print(f"❌ Ошибка получения метаданных: {e}")
        return None

    def _update_processing_progress(self, processing_id, completed_batches):
        """Обновляем прогресс обработки"""
        try:
            metadata = self._get_processing_metadata(processing_id)
            if metadata:
                metadata['completed_batches'] = completed_batches
                
                # Проверяем, завершена ли обработка
                if completed_batches >= metadata['total_batches']:
                    metadata['status'] = 'completed'
                    self._send_telegram_notification(
                        metadata['chat_id'],
                        f"🎉 <b>Обработка завершена!</b>\n"
                        f"📚 Книга: {metadata['book_title']}\n"
                        f"📊 Обработано блоков: {metadata['total_blocks']}\n"
                        f"💾 Книга сохранена в вашу библиотеку!\n"
                        f"📖 Теперь можете читать командой /more",
                        metadata['token']
                    )
                    
                    # Обновляем библиотеку пользователя
                    from books_library import BooksLibrary
                    books_lib = BooksLibrary()
                    books_lib.update_current_book(metadata['user_id'], metadata['chat_id'], metadata['book_id'])
                    books_lib.update_book_pos(metadata['user_id'], metadata['book_id'], 0)
                
                # Сохраняем обновленные метаданные
                update_query = f"""
                    UPDATE processing_metadata
                    SET metadata = '{json.dumps(metadata)}'
                    WHERE processing_id = '{processing_id}';
                """
                self.db.db_adapter.execute_query(update_query)
                
                # Отправляем промежуточное уведомление о прогрессе
                if completed_batches < metadata['total_batches']:
                    progress_percent = (completed_batches / metadata['total_batches']) * 100
                    self._send_telegram_notification(
                        metadata['chat_id'],
                        f"📊 Прогресс: {completed_batches}/{metadata['total_batches']} ({progress_percent:.1f}%)\n"
                        f"⚡ Продолжаю обработку...",
                        metadata['token']
                    )
                
        except Exception as e:
            print(f"❌ Ошибка обновления прогресса: {e}")

    def _send_batch_to_queue(self, processing_id, batch, book_id, sending_mode, token):
        """Отправляем батч в очередь для обработки"""
        try:
            batch_message = {
                'type': 'process_batch',
                'processing_id': processing_id,
                'batch_id': batch['batch_id'],
                'book_id': book_id,
                'blocks': batch['blocks'],
                'start_index': batch['start_index'],
                'end_index': batch['end_index'],
                'sending_mode': sending_mode,
                'token': token
            }
            
            # Отправляем в очередь (используем существующий QueueSender)
            success = self.queue_sender.send_batch_processing_message(batch_message)
            
            if success:
                print(f"✅ Батч {batch['batch_id']} отправлен в очередь")
            else:
                print(f"❌ Ошибка отправки батча {batch['batch_id']} в очередь")
                
        except Exception as e:
            print(f"❌ Ошибка отправки батча в очередь: {e}")

    def handle_batch_completion(self, processing_id, batch_id, chunks_created):
        """
        Обрабатываем завершение обработки батча
        
        Args:
            processing_id: ID обработки
            batch_id: ID завершенного батча
            chunks_created: Количество созданных чанков
        """
        try:
            print(f"✅ Батч {batch_id} завершен, создано чанков: {chunks_created}")
            
            # Получаем метаданные обработки
            metadata = self._get_processing_metadata(processing_id)
            if not metadata:
                print(f"❌ Метаданные обработки не найдены: {processing_id}")
                return
            
            # Увеличиваем счетчик завершенных батчей
            completed_batches = metadata.get('completed_batches', 0) + 1
            
            # Обновляем прогресс
            self._update_processing_progress(processing_id, completed_batches)
            
        except Exception as e:
            print(f"❌ Ошибка обработки завершения батча: {e}")


