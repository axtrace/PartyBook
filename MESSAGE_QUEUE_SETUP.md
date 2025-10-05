# Настройка Message Queue для асинхронной обработки книг

## 🎯 Цель
Реализовать асинхронную обработку EPUB книг без ограничений по времени выполнения функций.

## 🏗️ Архитектура

```
Пользователь → Telegram Bot → Message Queue → Processing Function → Database
     ↓              ↓              ↓                ↓
  Загружает    Отправляет в    Триггер        Обрабатывает
   книгу        очередь       запускает      полностью и
                мгновенно      функцию        уведомляет
```

## 📋 Шаги настройки

### 1. Создание Message Queue

1. Перейдите в **Yandex Cloud Console** → **Message Queue**
2. Создайте новую очередь:
   - **Имя**: `book-processing-queue`
   - **Тип**: Standard
   - **Регион**: ru-central1

3. Получите URL очереди и сохраните его

### 2. Настройка переменных окружения

Добавьте в переменные окружения основной функции:

```bash
# Message Queue настройки
MESSAGE_QUEUE_URL=https://message-queue.api.cloud.yandex.net/your-queue-url
AWS_REGION=ru-central1
```

**Примечание**: `AWS_ACCESS_KEY_ID` и `AWS_SECRET_ACCESS_KEY` уже настроены в ваших GitHub Actions секретах и будут автоматически использоваться.

### 3. Создание функции обработки

1. Создайте новую **Cloud Function**:
   - **Имя**: `book-processing-function`
   - **Runtime**: Python 3.9
   - **Entrypoint**: `queue_handler.handler`
   - **Memory**: 4096 MB
   - **Timeout**: 600 секунд (10 минут)

2. Загрузите код из файла `queue_handler.py` и всех зависимостей

### 4. Настройка триггера

1. Перейдите в **Cloud Functions** → **Триггеры**
2. Создайте новый триггер:
   - **Тип**: Message Queue
   - **Очередь**: `book-processing-queue`
   - **Функция**: `book-processing-function`
   - **Batch size**: 1
   - **Visibility timeout**: 600 секунд

### 5. Обновление основной функции

Замените код в основной функции на использование Message Queue:

```python
# В index.py
from book_adder import BookAdder

book_adder = BookAdder()

# В handle_document
book_id = book_adder.add_new_book(user_id, chat_id, local_file_path, sending_mode, bot)
```

## 🔧 Конфигурация

### Переменные окружения для основной функции:
```bash
TOKEN=your-telegram-bot-token
MESSAGE_QUEUE_URL=https://message-queue.api.cloud.yandex.net/your-queue-url
AWS_REGION=ru-central1
# AWS_ACCESS_KEY_ID и AWS_SECRET_ACCESS_KEY уже настроены в GitHub Actions
```

### Переменные окружения для функции обработки:
```bash
TOKEN=your-telegram-bot-token
# YDB настройки (те же, что и в основной функции)
YDB_ENDPOINT=your-ydb-endpoint
YDB_DATABASE=your-ydb-database
# AWS_ACCESS_KEY_ID и AWS_SECRET_ACCESS_KEY уже настроены в GitHub Actions
```

## 📊 Мониторинг

### Логи основной функции:
- Отправка сообщений в очередь
- Создание временных записей о книгах

### Логи функции обработки:
- Получение сообщений из очереди
- Обработка EPUB файлов
- Создание чанков в БД
- Отправка уведомлений пользователям

## 🚀 Преимущества решения

1. **Без ограничений по времени** - функция обработки может работать до 10 минут
2. **Мгновенный ответ пользователю** - книга ставится в очередь сразу
3. **Надежность** - сообщения в очереди гарантированно обрабатываются
4. **Масштабируемость** - можно запускать несколько экземпляров функции обработки
5. **Мониторинг** - полная видимость процесса через логи

## 🧪 Тестирование

### Локальное тестирование:
```bash
cd /Users/matvey/Documents/GitHub/PartyBook
python app/queue_handler.py
```

### Тестирование отправки в очередь:
```python
from queue_sender import QueueSender

sender = QueueSender()
success = sender.send_test_message()
print(f"Отправка тестового сообщения: {success}")
```

## 🔍 Отладка

### Проверка очереди:
1. Перейдите в **Message Queue** → ваша очередь
2. Проверьте количество сообщений
3. Просмотрите логи функции обработки

### Частые проблемы:
1. **Неправильный URL очереди** - проверьте переменную `MESSAGE_QUEUE_URL`
2. **Неправильные ключи доступа** - проверьте, что `AWS_ACCESS_KEY_ID` и `AWS_SECRET_ACCESS_KEY` правильно настроены в GitHub Actions секретах
3. **Триггер не настроен** - убедитесь, что триггер привязан к правильной очереди и функции
4. **Таймаут функции** - увеличьте timeout для функции обработки

## 📈 Масштабирование

При высокой нагрузке:
1. Увеличьте **batch size** триггера (до 10)
2. Увеличьте **memory** функции обработки (до 8GB)
3. Создайте несколько очередей для разных типов книг
4. Используйте **dead letter queue** для обработки ошибок
