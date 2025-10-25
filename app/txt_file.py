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
        # Разбиваем текст на предложения
        sentences = TextSeparator(text, mode=sent_mode).get_sentences()
        print(f"📝 Получено {len(sentences)} предложений")
        
        # Группируем предложения в чанки по 5 предложений
        sentences_per_chunk = 5
        chunks_to_save = []
        
        for i in range(0, len(sentences), sentences_per_chunk):
            # Берем следующие 5 предложений (или меньше, если это конец)
            chunk_sentences = sentences[i:i + sentences_per_chunk]
            current_chunk = ' '.join(chunk_sentences)
            
            if current_chunk.strip():
                chunks_to_save.append(current_chunk)
        
        # БАТЧИНГ: Сохраняем все чанки одним запросом
        if chunks_to_save:
            try:
                chunks_created = self.db.save_chunks_batch(book_id, chunks_to_save)
                print(f"✅ Создано {chunks_created} новых чанков (батчинг)")
                return chunks_created
            except Exception as e:
                print(f"❌ Ошибка батчинга чанков: {e}")
                # Fallback к старому методу
                return self._create_chunks_legacy(book_id, chunks_to_save)
        
        return 0
    
    def _create_chunks_legacy(self, book_id, chunks_to_save):
        """Fallback метод для совместимости"""
        current_chunk_count = self.db.get_total_chunks(book_id)
        chunk_id = current_chunk_count
        chunks_created = 0
        
        for chunk in chunks_to_save:
            try:
                self.db.save_chunk(book_id, chunk_id, chunk)
                chunk_id += 1
                chunks_created += 1
            except Exception as e:
                print(f"❌ Ошибка сохранения чанка {chunk_id}: {e}")
                break
        
        return chunks_created

    def read_piece(self, book_id, pos):
        # Получаем чанк из базы данных
        chunk = self.db.get_chunk(book_id, pos)
        if chunk is None:
            return None, pos
        
        return chunk, pos + 1

    def get_total_chunks(self, book_id):
        return self.db.get_total_chunks(book_id)
