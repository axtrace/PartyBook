#!/usr/bin/env python3
"""
Обработчик батчей для параллельной обработки книг
Эта функция обрабатывает один батч текстовых блоков
"""

import json
import os
from txt_file import BookChunkManager
from parallel_book_processor import ParallelBookProcessor


class BatchProcessor(object):
    """Обработчик одного батча текстовых блоков"""

    def __init__(self):
        self.chunk_manager = BookChunkManager()
        self.parallel_processor = ParallelBookProcessor()

    def process_batch(self, batch_data):
        """
        Обрабатывает один батч текстовых блоков
        
        Args:
            batch_data: Данные батча из очереди
            
        Returns:
            dict: Результат обработки батча
        """
        try:
            print(f"🔄 Начинаем обработку батча: {batch_data.get('batch_id')}")
            
            # Извлекаем данные из батча
            processing_id = batch_data.get('processing_id')
            batch_id = batch_data.get('batch_id')
            book_id = batch_data.get('book_id')
            blocks = batch_data.get('blocks', [])
            sending_mode = batch_data.get('sending_mode', 'by_sense')
            start_index = batch_data.get('start_index', 0)
            end_index = batch_data.get('end_index', 0)
            
            print(f"📊 Батч {batch_id}: блоки {start_index}-{end_index}, всего {len(blocks)} блоков")
            
            if not blocks:
                print(f"⚠️ Батч {batch_id} пустой, пропускаем")
                return {
                    'success': True,
                    'batch_id': batch_id,
                    'chunks_created': 0,
                    'blocks_processed': 0
                }
            
            # Обрабатываем каждый блок в батче
            total_chunks_created = 0
            blocks_processed = 0
            
            for i, text_block in enumerate(blocks):
                if text_block and text_block.strip():
                    try:
                        print(f"🔄 Обрабатываем блок {start_index + i + 1} (длина: {len(text_block)} символов)")
                        
                        # Создаем чанки из блока
                        chunks_created = self.chunk_manager.create_chunks(book_id, text_block, sending_mode)
                        total_chunks_created += chunks_created
                        blocks_processed += 1
                        
                        print(f"✅ Блок {start_index + i + 1} обработан, создано чанков: {chunks_created}")
                        
                    except Exception as e:
                        print(f"❌ Ошибка обработки блока {start_index + i + 1}: {e}")
                        # Продолжаем обработку других блоков
                else:
                    print(f"⚠️ Пустой блок {start_index + i + 1}, пропускаем")
            
            print(f"✅ Батч {batch_id} завершен: обработано {blocks_processed} блоков, создано {total_chunks_created} чанков")
            
            # Уведомляем координатор о завершении батча
            self.parallel_processor.handle_batch_completion(processing_id, batch_id, total_chunks_created)
            
            return {
                'success': True,
                'batch_id': batch_id,
                'chunks_created': total_chunks_created,
                'blocks_processed': blocks_processed
            }
            
        except Exception as e:
            print(f"❌ Критическая ошибка обработки батча {batch_id}: {e}")
            import traceback
            print(f"❌ Traceback: {traceback.format_exc()}")
            return {
                'success': False,
                'batch_id': batch_id,
                'error': str(e)
            }

    def process_batch_from_queue(self, event, context):
        """
        Обрабатывает сообщения о батчах из очереди
        
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
                    # Декодируем сообщение из Yandex Message Queue
                    if 'details' in message and 'message' in message['details'] and 'body' in message['details']['message']:
                        batch_data = json.loads(message['details']['message']['body'])
                    elif 'data' in message:
                        batch_data = json.loads(message['data'])
                    else:
                        print(f"❌ Нет данных в сообщении: {message}")
                        continue
                    
                    print(f"📦 Обрабатываем батч: {batch_data.get('batch_id')}")
                    
                    # Обрабатываем батч
                    result = self.process_batch(batch_data)
                    
                    print(f"✅ Результат обработки батча: {result}")
            
            return {'statusCode': 200, 'body': 'Batch processing completed'}
            
        except Exception as e:
            print(f"❌ Ошибка обработки сообщения о батче: {e}")
            import traceback
            print(f"❌ Traceback: {traceback.format_exc()}")
            return {'statusCode': 500, 'body': f'Error: {str(e)}'}


def handler(event, context):
    """
    Главная функция-обработчик для обработки батчей
    
    Args:
        event: Событие от Message Queue с данными батча
        context: Контекст выполнения функции
        
    Returns:
        dict: Результат обработки
    """
    print(f"🔄 Получено событие для обработки батча")
    print(f"📨 Событие: {event}")
    
    try:
        # Создаем процессор батчей
        processor = BatchProcessor()
        
        # Парсим сообщение из очереди
        if 'messages' in event:
            for message in event['messages']:
                # Декодируем сообщение из Yandex Message Queue
                if 'details' in message and 'message' in message['details'] and 'body' in message['details']['message']:
                    batch_data = json.loads(message['details']['message']['body'])
                elif 'data' in message:
                    batch_data = json.loads(message['data'])
                else:
                    print(f"❌ Нет данных в сообщении: {message}")
                    continue
                
                print(f"📦 Обрабатываем батч: {batch_data.get('batch_id')}")
                
                # Обрабатываем батч
                result = processor.process_batch(batch_data)
                
                print(f"✅ Результат обработки батча: {result}")
        
        return {'statusCode': 200, 'body': 'Batch processing completed'}
        
    except Exception as e:
        print(f"❌ Критическая ошибка в обработчике батчей: {e}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
        return {
            'statusCode': 500,
            'body': f'Critical error: {str(e)}'
        }


if __name__ == "__main__":
    # Для локального тестирования
    test_batch_data = {
        'processing_id': 'test-processing-123',
        'batch_id': 'test-processing-123_batch_0',
        'book_id': 1,
        'blocks': [
            'Это первый блок текста для тестирования.',
            'Это второй блок текста для тестирования.',
            'Это третий блок текста для тестирования.'
        ],
        'start_index': 0,
        'end_index': 2,
        'sending_mode': 'by_sense',
        'token': 'test_token'
    }
    
    test_event = {
        'messages': [
            {
                'data': json.dumps(test_batch_data)
            }
        ]
    }
    
    test_context = {}
    
    result = handler(test_event, test_context)
    print(f"Результат тестирования: {result}")
