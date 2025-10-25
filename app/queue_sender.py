import json
import boto3
import os
from botocore.exceptions import ClientError


class QueueSender(object):
    """Отправитель сообщений в Message Queue для асинхронной обработки книг"""

    def __init__(self):
        # Настройки для Yandex Message Queue
        self.queue_url = os.environ.get('MESSAGE_QUEUE_URL')
        self.aws_access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
        self.aws_secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
        self.region_name = os.environ.get('AWS_REGION', 'ru-central1')
        
        # Создаем клиент SQS (совместимый с Yandex Message Queue)
        self.sqs_client = boto3.client(
            'sqs',
            endpoint_url='https://message-queue.api.cloud.yandex.net',
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name=self.region_name
        )

    def send_book_processing_message(self, user_id, chat_id, epub_path, sending_mode, token):
        """
        Отправляем сообщение в очередь для обработки книги
        
        Args:
            user_id: ID пользователя
            chat_id: ID чата
            epub_path: Путь к EPUB файлу
            sending_mode: Режим обработки текста
            token: Токен бота для уведомлений
            
        Returns:
            bool: True если сообщение отправлено успешно
        """
        try:
            if not self.queue_url:
                print(f"❌ MESSAGE_QUEUE_URL не настроен")
                return False
            
            # Формируем сообщение
            message_data = {
                'user_id': user_id,
                'chat_id': chat_id,
                'epub_path': epub_path,
                'sending_mode': sending_mode,
                'token': token,
                'timestamp': str(int(time.time()))
            }
            
            message_body = json.dumps(message_data)
            
            print(f"📤 Отправляем сообщение в очередь: {self.queue_url}")
            print(f"📨 Данные сообщения: {message_data}")
            
            # Отправляем сообщение
            response = self.sqs_client.send_message(
                QueueUrl=self.queue_url,
                MessageBody=message_body,
                MessageAttributes={
                    'MessageType': {
                        'StringValue': 'book_processing',
                        'DataType': 'String'
                    },
                    'UserId': {
                        'StringValue': str(user_id),
                        'DataType': 'String'
                    }
                }
            )
            
            print(f"✅ Сообщение отправлено успешно: {response['MessageId']}")
            return True
            
        except ClientError as e:
            print(f"❌ Ошибка отправки сообщения в очередь: {e}")
            return False
        except Exception as e:
            print(f"❌ Неожиданная ошибка: {e}")
            return False

    def send_batch_processing_message(self, batch_data):
        """
        Отправляем сообщение в очередь для обработки батча
        
        Args:
            batch_data: Данные батча для обработки
            
        Returns:
            bool: True если сообщение отправлено успешно
        """
        try:
            if not self.queue_url:
                print(f"❌ MESSAGE_QUEUE_URL не настроен")
                return False
            
            # Добавляем timestamp
            batch_data['timestamp'] = str(int(time.time()))
            
            message_body = json.dumps(batch_data)
            
            print(f"📤 Отправляем батч в очередь: {batch_data.get('batch_id')}")
            print(f"📦 Батч содержит {len(batch_data.get('blocks', []))} блоков")
            
            # Отправляем сообщение
            response = self.sqs_client.send_message(
                QueueUrl=self.queue_url,
                MessageBody=message_body,
                MessageAttributes={
                    'MessageType': {
                        'StringValue': 'batch_processing',
                        'DataType': 'String'
                    },
                    'ProcessingId': {
                        'StringValue': batch_data.get('processing_id', 'unknown'),
                        'DataType': 'String'
                    },
                    'BatchId': {
                        'StringValue': batch_data.get('batch_id', 'unknown'),
                        'DataType': 'String'
                    }
                }
            )
            
            print(f"✅ Батч отправлен успешно: {response['MessageId']}")
            return True
            
        except ClientError as e:
            print(f"❌ Ошибка отправки батча в очередь: {e}")
            return False
        except Exception as e:
            print(f"❌ Неожиданная ошибка при отправке батча: {e}")
            return False

    def send_test_message(self):
        """Отправляем тестовое сообщение для проверки подключения"""
        try:
            test_data = {
                'user_id': 12345,
                'chat_id': 12345,
                'epub_path': '/tmp/test.epub',
                'sending_mode': 'by_sense',
                'token': 'test_token',
                'timestamp': str(int(time.time()))
            }
            
            message_body = json.dumps(test_data)
            
            response = self.sqs_client.send_message(
                QueueUrl=self.queue_url,
                MessageBody=message_body
            )
            
            print(f"✅ Тестовое сообщение отправлено: {response['MessageId']}")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка отправки тестового сообщения: {e}")
            return False


# Импортируем time для timestamp
import time

