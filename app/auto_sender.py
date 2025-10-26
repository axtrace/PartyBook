#!/usr/bin/env python3
"""
Автоматическая отправка чанков пользователям
Эта функция будет вызываться триггером по расписанию
"""

import os
import json
import requests
from datetime import datetime
from db_manager import DbManager
from shared_functions import send_portion
import config


class AutoSender:
    """Класс для автоматической отправки чанков пользователям"""
    
    def __init__(self):
        self.db = DbManager()
        self.bot_token = os.environ.get('TOKEN')
        if not self.bot_token:
            raise ValueError("TOKEN environment variable not set")
    
    def get_users_for_auto_send_by_time(self, current_time):
        """
        Получает пользователей для автопересылки по их предпочтительному времени
        
        Args:
            current_time: Текущее время (datetime)
            
        Returns:
            list: Список пользователей с их данными
        """
        return self.db.get_users_for_auto_send_by_time(current_time)
    
    def send_portion_to_user(self, user_id, chat_id, lang='ru'):
        """
        Отправляет следующий чанк пользователю
        Использует общую функцию send_portion из shared_functions
        
        Args:
            user_id: ID пользователя
            chat_id: ID чата
            lang: Язык пользователя
            
        Returns:
            dict: Результат отправки
        """
        try:
            print(f"📤 Отправляем чанк пользователю {user_id}")
            
            # Используем общую функцию send_portion (bot=None для автопересылки)
            result = send_portion(user_id, chat_id, bot=None)
            
            if isinstance(result, dict):
                # Результат от общей функции для автопересылки
                if result['success']:
                    # Отправляем сообщение через Telegram API
                    self._send_telegram_message(chat_id, result['message'])
                    print(f"✅ Чанк отправлен пользователю {user_id}")
                    return {'success': True}
                else:
                    # Ошибка - отправляем сообщение об ошибке
                    if 'message' in result:
                        self._send_telegram_message(chat_id, result['message'])
                    return result
            else:
                # Старый формат результата (0/-1)
                if result == 0:
                    return {'success': True}
                else:
                    return {'success': False, 'reason': 'unknown_error'}
                    
        except Exception as e:
            print(f"❌ Ошибка отправки чанка пользователю {user_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def _send_telegram_message(self, chat_id, text):
        """
        Отправляет сообщение в Telegram
        
        Args:
            chat_id: ID чата
            text: Текст сообщения
        """
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        
        # Разбиваем длинные сообщения на части
        max_telegram_size = 4096
        for i in range(0, len(text), max_telegram_size):
            chunk = text[i:i+max_telegram_size]
            
            payload = {
                'chat_id': chat_id,
                'text': chunk,
                'parse_mode': 'HTML'
            }
            
            try:
                response = requests.post(url, json=payload, timeout=10)
                response.raise_for_status()
                print(f"✅ Сообщение отправлено в чат {chat_id}")
            except Exception as e:
                print(f"❌ Ошибка отправки в чат {chat_id}: {e}")
                raise
    
    
    def process_auto_send(self, current_time):
        """
        Основная функция обработки автопересылки
        
        Args:
            current_time: Текущее время
            
        Returns:
            dict: Статистика обработки
        """
        print(f"🚀 Начинаем автопересылку в {current_time.strftime('%H:%M')}")
        
        # Получаем пользователей для отправки по их предпочтительному времени
        users = self.get_users_for_auto_send_by_time(current_time)
        
        if not users:
            print("📭 Нет пользователей для автопересылки")
            return {
                'success': True,
                'users_processed': 0,
                'successful_sends': 0,
                'errors': 0
            }
        
        # Обрабатываем каждого пользователя
        successful_sends = 0
        errors = 0
        
        for user in users:
            try:
                result = self.send_portion_to_user(
                    user['user_id'], 
                    user['chat_id'], 
                    user['lang']
                )
                
                if result['success']:
                    successful_sends += 1
                else:
                    errors += 1
                    print(f"⚠️ Не удалось отправить пользователю {user['user_id']}: {result.get('reason', 'unknown')}")
                    
            except Exception as e:
                errors += 1
                print(f"❌ Критическая ошибка для пользователя {user['user_id']}: {e}")
        
        stats = {
            'success': True,
            'users_processed': len(users),
            'successful_sends': successful_sends,
            'errors': errors,
            'current_time': current_time.isoformat(),
            'time_slot': current_time.strftime('%H:%M')
        }
        
        print(f"📊 Статистика автопересылки: {stats}")
        return stats


def handler(event, context):
    """
    Главная функция-обработчик для триггера автопересылки
    
    Args:
        event: Событие от триггера
        context: Контекст выполнения функции
        
    Returns:
        dict: Результат обработки
    """
    print(f"🔄 Получено событие автопересылки: {event}")
    
    try:
        # Получаем текущее время
        current_time = datetime.now()
        
        # Создаем отправитель и обрабатываем
        auto_sender = AutoSender()
        result = auto_sender.process_auto_send(current_time)
        
        print(f"✅ Автопересылка завершена: {result}")
        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }
        
    except Exception as e:
        print(f"❌ Критическая ошибка автопересылки: {e}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


if __name__ == "__main__":
    # Для локального тестирования
    test_event = {}
    test_context = {}
    
    result = handler(test_event, test_context)
    print(f"Результат тестирования: {result}")
