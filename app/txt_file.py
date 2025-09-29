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
        
        # Группируем предложения в чанки по 5 предложений
        sentences_per_chunk = 5
        chunk_id = current_chunk_count  # Начинаем с существующего количества
        chunks_created = 0
        
        for i in range(0, len(sentences), sentences_per_chunk):
            # Берем следующие 5 предложений (или меньше, если это конец)
            chunk_sentences = sentences[i:i + sentences_per_chunk]
            current_chunk = ' '.join(chunk_sentences)
            
            if current_chunk.strip():
                try:
                    self.db.save_chunk(book_id, chunk_id, current_chunk)
                    print(f"💾 Сохранен чанк {chunk_id} длиной {len(current_chunk)} символов ({len(chunk_sentences)} предложений)")
                    chunk_id += 1
                    chunks_created += 1
                except Exception as e:
                    print(f"❌ Ошибка сохранения чанка {chunk_id}: {e}")
                    return chunks_created
        
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
