import os
import json
from epub_reader import EpubReader
from txt_file import BookChunkManager
from db_manager import DbManager
from text_transliter import TextTransliter


class AsyncEpubProcessor(object):
    """Асинхронный процессор EPUB файлов для облачной среды"""

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

    def _save_processing_state(self, book_id, epub_path, processed_items, total_items, current_item_index):
        """Сохраняем состояние обработки в БД"""
        state = {
            'epub_path': epub_path,
            'processed_items': processed_items,
            'total_items': total_items,
            'current_item_index': current_item_index,
            'status': 'processing'
        }
        
        query = f"""
            UPDATE books 
            SET processingState = '{json.dumps(state)}'
            WHERE id = {book_id};
        """
        
        try:
            self.db.db_adapter.execute_query(query)
            print(f"💾 Состояние обработки сохранено: {current_item_index}/{total_items}")
        except Exception as e:
            print(f"❌ Ошибка сохранения состояния: {e}")

    def _get_processing_state(self, book_id):
        """Получаем состояние обработки из БД"""
        query = f"""
            SELECT processingState FROM books
            WHERE id = {book_id};
        """
        
        try:
            result = self.db.db_adapter.execute_query(query)
            if result and len(result[0].rows) > 0:
                state_str = str(result[0].rows[0][0])
                if state_str and state_str != 'None':
                    return json.loads(state_str)
        except Exception as e:
            print(f"❌ Ошибка получения состояния: {e}")
        
        return None

    def _clear_processing_state(self, book_id):
        """Очищаем состояние обработки"""
        query = f"""
            UPDATE books 
            SET processingState = NULL
            WHERE id = {book_id};
        """
        
        try:
            self.db.db_adapter.execute_query(query)
            print(f"✅ Состояние обработки очищено")
        except Exception as e:
            print(f"❌ Ошибка очистки состояния: {e}")

    def start_epub_processing(self, user_id, epub_path, sending_mode='by_sense', bot=None, chat_id=None):
        """
        Начинаем обработку EPUB файла (первый вызов)
        """
        try:
            print(f"🚀 Начинаем асинхронную обработку EPUB: {epub_path}")
            
            # Читаем EPUB файл
            book_reader = EpubReader(epub_path)
            book_title = book_reader.get_booktitle()
            print(f"📚 Название книги: {book_title}")
            
            if not book_title:
                raise ValueError("Could not extract book title from EPUB")
            
            # Создаем книгу в БД
            book_name = self._make_filename(user_id, book_title)
            book_id = self.db.get_or_create_book(book_name)
            
            if book_id is None:
                raise ValueError(f"Не удалось создать книгу: {book_name}")
            
            # Получаем общее количество элементов
            total_items = len(book_reader.item_ids)
            print(f"📊 Всего элементов для обработки: {total_items}")
            
            # Отправляем начальное сообщение
            self._send_progress_message(bot, chat_id, 
                f"📚 Начинаю обработку книги: {book_title}\n📊 Элементов: {total_items}\n⏱️ Обработка займет несколько этапов...")
            
            # Сохраняем начальное состояние
            self._save_processing_state(book_id, epub_path, [], total_items, 0)
            
            # Обрабатываем первый батч
            return self.continue_epub_processing(book_id, sending_mode, bot, chat_id)
            
        except Exception as e:
            print(f"❌ Error starting EPUB processing: {str(e)}")
            import traceback
            print(f"❌ Traceback: {traceback.format_exc()}")
            return None

    def continue_epub_processing(self, book_id, sending_mode='by_sense', bot=None, chat_id=None):
        """
        Продолжаем обработку EPUB файла (последующие вызовы)
        """
        try:
            print(f"🔄 Продолжаем обработку книги ID: {book_id}")
            
            # Получаем состояние обработки
            state = self._get_processing_state(book_id)
            if not state:
                print(f"❌ Состояние обработки не найдено для книги {book_id}")
                return None
            
            epub_path = state['epub_path']
            processed_items = state['processed_items']
            total_items = state['total_items']
            current_item_index = state['current_item_index']
            
            print(f"📊 Состояние: {current_item_index}/{total_items} элементов обработано")
            
            # Создаем новый reader для продолжения
            book_reader = EpubReader(epub_path)
            
            # Пропускаем уже обработанные элементы
            for i in range(current_item_index):
                if len(book_reader.item_ids) > 0:
                    book_reader.item_ids.pop(0)
            
            # Обрабатываем батч элементов (максимум 5 за раз)
            batch_size = 5
            processed_in_batch = 0
            total_chunks_created = 0
            
            while (len(book_reader.item_ids) > 0 and 
                   processed_in_batch < batch_size and 
                   current_item_index < total_items):
                
                print(f"🔄 Обрабатываем элемент {current_item_index + 1}/{total_items}")
                
                text = book_reader.get_next_item_text()
                if text and text.strip():
                    try:
                        chunks_created = self.chunk_manager.create_chunks(book_id, text, sending_mode)
                        total_chunks_created += chunks_created
                        processed_items.append(current_item_index)
                        processed_in_batch += 1
                        current_item_index += 1
                        
                        print(f"✅ Обработан элемент {current_item_index}, создано чанков: {chunks_created}")
                        
                    except Exception as e:
                        print(f"❌ Ошибка обработки элемента {current_item_index}: {e}")
                        current_item_index += 1
                else:
                    print(f"⚠️ Пустой элемент {current_item_index}, пропускаем")
                    current_item_index += 1
            
            # Проверяем, завершена ли обработка
            if current_item_index >= total_items:
                # Обработка завершена
                self._clear_processing_state(book_id)
                self._send_progress_message(bot, chat_id, 
                    f"🎉 Обработка книги завершена!\n📊 Всего элементов: {total_items}\n📚 Создано чанков: {total_chunks_created}")
                print(f"🎉 Обработка книги {book_id} полностью завершена!")
                return book_id
            else:
                # Сохраняем прогресс и планируем следующий вызов
                self._save_processing_state(book_id, epub_path, processed_items, total_items, current_item_index)
                
                progress_percent = (current_item_index / total_items) * 100
                self._send_progress_message(bot, chat_id, 
                    f"📊 Прогресс: {current_item_index}/{total_items} ({progress_percent:.1f}%)\n⏱️ Продолжаю обработку...")
                
                print(f"📊 Обработано в этом батче: {processed_in_batch}, всего: {current_item_index}/{total_items}")
                
                # Возвращаем book_id для продолжения обработки
                return book_id
                
        except Exception as e:
            print(f"❌ Error continuing EPUB processing: {str(e)}")
            import traceback
            print(f"❌ Traceback: {traceback.format_exc()}")
            return None

    def process_epub_async(self, user_id, epub_path, sending_mode='by_sense', bot=None, chat_id=None):
        """
        Главная функция для асинхронной обработки EPUB
        Автоматически определяет, начинать ли новую обработку или продолжать существующую
        """
        try:
            # Создаем имя книги для поиска
            book_reader = EpubReader(epub_path)
            book_title = book_reader.get_booktitle()
            book_name = self._make_filename(user_id, book_title)
            
            # Ищем существующую книгу
            book_id = self.db.get_or_create_book(book_name)
            
            if book_id is None:
                print(f"❌ Не удалось создать/найти книгу: {book_name}")
                return None
            
            # Проверяем, есть ли активная обработка
            state = self._get_processing_state(book_id)
            
            if state and state.get('status') == 'processing':
                # Продолжаем существующую обработку
                print(f"🔄 Продолжаем существующую обработку книги {book_id}")
                return self.continue_epub_processing(book_id, sending_mode, bot, chat_id)
            else:
                # Начинаем новую обработку
                print(f"🚀 Начинаем новую обработку книги {book_id}")
                return self.start_epub_processing(user_id, epub_path, sending_mode, bot, chat_id)
                
        except Exception as e:
            print(f"❌ Error in async EPUB processing: {str(e)}")
            import traceback
            print(f"❌ Traceback: {traceback.format_exc()}")
            return None
