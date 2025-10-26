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
from books_library import BooksLibrary
from txt_file import BookChunkManager
import config


class AutoSender:
    """Класс для автоматической отправки чанков пользователям"""
    
    def __init__(self):
        self.db = DbManager()
        self.books_lib = BooksLibrary()
        self.chunk_manager = BookChunkManager()
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
        # Получаем текущее время в формате HH:MM
        current_time_str = current_time.strftime("%H:%M")
        
        # Получаем всех пользователей с включенной автопересылкой
        query = f"""
            SELECT userId, chatId, lang, time FROM users
            WHERE isAutoSend = true 
            AND time != ""
            AND time = "{current_time_str}";
        """
        
        result = self.db.db_adapter.execute_query(query)
        users = []
        
        if result and len(result[0].rows) > 0:
            for row in result[0].rows:
                try:
                    data = self.db._text_to_json(str(row))
                    users.append({
                        'user_id': data['userId'],
                        'chat_id': data['chatId'],
                        'lang': data.get('lang', 'ru'),
                        'time': data['time']
                    })
                except Exception as e:
                    print(f"❌ Ошибка парсинга данных пользователя: {e}")
                    continue
        
        print(f"📊 Найдено {len(users)} пользователей для автопересылки в {current_time_str}")
        return users
    
    def send_portion_to_user(self, user_id, chat_id, lang='ru'):
        """
        Отправляет следующий чанк пользователю
        
        Args:
            user_id: ID пользователя
            chat_id: ID чата
            lang: Язык пользователя
            
        Returns:
            dict: Результат отправки
        """
        try:
            print(f"📤 Отправляем чанк пользователю {user_id}")
            
            # Получаем информацию о текущей книге пользователя
            book_info = self.books_lib.get_current_book(user_id)
            if not book_info or len(book_info) < 3:
                # Нет активной книги
                error_msg = config.error_user_finding.get(lang, config.error_user_finding['ru'])
                self._send_telegram_message(chat_id, error_msg)
                return {'success': False, 'reason': 'no_active_book'}
            
            book_id, book_name, pos = book_info[0], book_info[1], book_info[2]
            
            # Получаем следующий чанк текста
            text_piece, new_pos = self.chunk_manager.read_piece(book_id, pos)
            
            # Если чанк не найден, проверяем, не закончилась ли книга
            if text_piece is None:
                total_chunks = self.chunk_manager.get_total_chunks(book_id)
                if pos >= total_chunks:
                    # Книга закончена
                    finished_text = config.message_book_finished.get(lang, config.message_book_finished['ru'])
                    msg = config.end_book_string + f"\n{finished_text}\n/start_auto\n/my_books"
                    
                    # Отключаем автопересылку
                    self.db.update_auto_status(user_id, False)
                    print(f"📚 Книга пользователя {user_id} закончена, автопересылка отключена")
                    
                    self._send_telegram_message(chat_id, msg)
                    return {'success': True, 'reason': 'book_finished'}
                else:
                    # Ошибка получения чанка
                    error_msg = config.error_user_finding.get(lang, config.error_user_finding['ru'])
                    self._send_telegram_message(chat_id, error_msg)
                    return {'success': False, 'reason': 'chunk_error'}
            
            # Проверяем, закончена ли книга по содержимому
            if text_piece == config.end_book_string:
                finished_text = config.message_book_finished.get(lang, config.message_book_finished['ru'])
                msg = text_piece + f"\n{finished_text}\n/start_auto\n/my_books"
                
                # Отключаем автопересылку
                self.db.update_auto_status(user_id, False)
                print(f"📚 Книга пользователя {user_id} закончена, автопересылка отключена")
                
                self._send_telegram_message(chat_id, msg)
                return {'success': True, 'reason': 'book_finished'}
            
            # Отправляем чанк
            self._send_telegram_message(chat_id, text_piece)
            
            # Обновляем позицию в книге
            self.books_lib.update_book_pos(user_id, book_id, new_pos)
            
            print(f"✅ Чанк отправлен пользователю {user_id}, следующая позиция: {new_pos}")
            return {'success': True, 'next_pos': new_pos}
            
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
