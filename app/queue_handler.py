#!/usr/bin/env python3
"""
Обработчик сообщений из Message Queue для Yandex Cloud Functions
Эта функция будет вызываться триггером при поступлении сообщений в очередь
"""

from message_queue_processor import MessageQueueProcessor


def handler(event, context):
    """
    Главная функция-обработчик для триггера Message Queue
    
    Args:
        event: Событие от Message Queue
        context: Контекст выполнения функции
        
    Returns:
        dict: Результат обработки
    """
    print(f"🔄 Получено событие от Message Queue триггера")
    print(f"📨 Событие: {event}")
    print(f"🔧 Контекст: {context}")
    
    try:
        # Создаем процессор сообщений
        processor = MessageQueueProcessor()
        
        # Обрабатываем сообщения
        result = processor.process_book_from_queue(event, context)
        
        print(f"✅ Обработка завершена: {result}")
        return result
        
    except Exception as e:
        print(f"❌ Критическая ошибка в обработчике очереди: {e}")
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
                'data': '{"user_id": 12345, "chat_id": 12345, "epub_path": "/tmp/test.epub", "sending_mode": "by_sense", "token": "test_token"}'
            }
        ]
    }
    
    test_context = {}
    
    result = handler(test_event, test_context)
    print(f"Результат тестирования: {result}")