import json
import telebot
import os
import boto3

# Получаем токен бота из переменных окружения
token = os.environ['TEST_TOKEN']

bot = telebot.TeleBot(token)

s3 = boto3.client('s3',
    endpoint_url='https://storage.yandexcloud.net',
    aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
    aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY']
)

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
        file_url = bot.get_file_url(file_info.file_id)  # <-- Используем метод telebot

        response = requests.get(file_url)
        if response.ok:
            s3.put_object(
                Bucket=os.environ['BUCKET_NAME'],
                Key=message.document.file_name,
                Body=response.content,
                ContentType=message.document.mime_type
            )
            bot.reply_to(message, "✅ Файл успешно загружен в S3")
        else:
            bot.reply_to(message, f"❌ Ошибка {response.status_code} при загрузке файла")

    except Exception as e:
        bot.reply_to(message, f"⚠️ Ошибка: {str(e)}")
        logger.error(f"File processing error: {e}")

@bot.message_handler(content_types=['text'])
def handle_text(message):

    # Получаем идентификатор чата
    chat_id = message.chat.id

    # Отправляем ответ "privet"
    bot.reply_to(message, "privet-privet")



