import json
import telebot
import os


def handler(event, context):
    # Получаем токен бота из переменных окружения
    token = os.environ['TEST_TOKEN']
    bot = telebot.TeleBot(token)

    # Парсим входящее сообщение
    update = telebot.types.Update.de_json(json.loads(event['body']))

    # Получаем идентификатор чата
    chat_id = update.message.chat.id

    # Отправляем ответ "privet"
    bot.send_message(chat_id, "privet")

    return {
        'statusCode': 200,
        'body': 'OK'
    }