import os
import errno
from time import gmtime, strftime
from text_separator import TextSeparator
import config
from db_manager import DbManager

class BookChunkManager(object):
    """
    Class for managing book text chunks in YDB
    """

    def __init__(self):
        self.db = DbManager()
        self.chunk_size = config.piece_size

    def create_chunks(self, book_id, text, sent_mode):
        # Получаем текущее количество чанков для этой книги
        current_chunk_count = self.db.get_total_chunks(book_id)
        print(f"📊 Текущее количество чанков для книги {book_id}: {current_chunk_count}")
        
        # Разбиваем текст на предложения
        sentences = TextSeparator(text, mode=sent_mode).get_sentences()
        print(f"📝 Получено {len(sentences)} предложений")
        
        # Группируем предложения в чанки
        current_chunk = ""
        chunk_id = current_chunk_count  # Начинаем с существующего количества
        
        chunks_created = 0
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) > self.chunk_size:
                # Сохраняем текущий чанк
                try:
                    self.db.save_chunk(book_id, chunk_id, current_chunk)
                    print(f"💾 Сохранен чанк {chunk_id} длиной {len(current_chunk)} символов")
                    chunk_id += 1
                    chunks_created += 1
                    current_chunk = sentence
                except Exception as e:
                    print(f"❌ Ошибка сохранения чанка {chunk_id}: {e}")
                    return chunks_created
            else:
                current_chunk += sentence
        
        # Сохраняем последний чанк
        if current_chunk:
            try:
                self.db.save_chunk(book_id, chunk_id, current_chunk)
                print(f"💾 Сохранен последний чанк {chunk_id} длиной {len(current_chunk)} символов")
                chunks_created += 1
            except Exception as e:
                print(f"❌ Ошибка сохранения последнего чанка {chunk_id}: {e}")
        
        print(f"✅ Создано {chunks_created} новых чанков")
        return chunks_created

    def read_piece(self, book_id, pos):
        # Получаем чанк из базы данных
        chunk = self.db.get_chunk(book_id, pos)
        if chunk is None:
            return None, pos
        
        return chunk, pos + 1

    def get_total_chunks(self, book_id):
        return self.db.get_total_chunks(book_id)
