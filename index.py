import json
import telebot
import os
import boto3
import requests
import s3_adapter

# Получаем токен бота из переменных окружения
token = os.environ['TEST_TOKEN']

bot = telebot.TeleBot(token)

s3a = s3_adapter.s3Adapter()

def handler(event, context):
    message = telebot.types.Update.de_json(event['body'])
    bot.process_new_updates([message])
    return {
        'statusCode': 200,
        'body': 'OK'
    }

@bot.message_handler(content_types=['document'])
def handle_document(message):
    try:
        file_info = bot.get_file(message.document.file_id)
        file_url = bot.get_file_url(file_info.file_id)

        response = requests.get(file_url)

        if response.ok:
            filename = message.document.file_name
            mime_type = message.document.mime_type
            body = response.content

            s3a.put_object(filename, body, mime_type)
            obj = s3a.get_object(filename)

            bot.reply_to(message, "✅ Файл успешно загружен в S3" + str(obj))
        else:
            bot.reply_to(message, f"❌ Ошибка {response.status_code} при загрузке файла")

    except Exception as e:
        bot.reply_to(message, f"⚠️ Ошибка: {str(e)}")

@bot.message_handler(content_types=['text'])
def handle_text(message):
    try:
        chat_id = message.chat.id
        bot.reply_to(message, "privet-privet")

    except Exception as e:
        bot.reply_to(message, f"⚠️ Ошибка: {str(e)}")