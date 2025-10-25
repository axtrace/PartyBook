#!/usr/bin/env python3
"""
Обработчик сообщений из Message Queue для параллельной обработки батчей
Эта функция будет вызываться триггером при поступлении сообщений о батчах
"""

from batch_processor import BatchProcessor


def handler(event, context):
    """
    Главная функция-обработчик для триггера Message Queue (батчи)
    
    Args:
        event: Событие от Message Queue
        context: Контекст выполнения функции
        
    Returns:
        dict: Результат обработки
    """
    print(f"🔄 Получено событие от Message Queue триггера (батчи)")
    print(f"📨 Событие: {event}")
    print(f"🔧 Контекст: {context}")
    
    try:
        # Создаем процессор батчей
        processor = BatchProcessor()
        
        # Обрабатываем сообщения
        result = processor.process_batch_from_queue(event, context)
        
        print(f"✅ Обработка батча завершена: {result}")
        return result
        
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
    test_event = {
        'messages': [
            {
                'data': '{"type": "process_batch", "processing_id": "test-123", "batch_id": "test-123_batch_0", "book_id": 1, "blocks": ["Test block 1", "Test block 2"], "sending_mode": "by_sense", "token": "test_token"}'
            }
        ]
    }
    
    test_context = {}
    
    result = handler(test_event, test_context)
    print(f"Результат тестирования: {result}")


