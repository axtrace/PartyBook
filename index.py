import json
import telebot
import os
import boto3
import requests
import s3_adapter

# Получаем токен бота из переменных окружения (для тестирования или для продакшена)
token = os.environ['TOKEN']

bot = telebot.TeleBot(token)

s3a = s3_adapter.s3Adapter()

def handler(event, context):
    message = telebot.types.Update.de_json(event['body'])
    bot.process_new_updates([message])
    return {
        'statusCode': 200,
        'body': 'OK'
    }

@bot.message_handler(commands=['more'])
def more_handler(message):
    try:
        bot.reply_to(message, "more")
    except Exception as e:
        bot.reply_to(message, f"⚠️ Ошибка: {str(e)}")

@bot.message_handler(commands=['help'])
def help_handler(message):
    try:
        bot.reply_to(message, "help")
    except Exception as e:
        bot.reply_to(message, f"⚠️ Ошибка: {str(e)}")

@bot.message_handler(commands=['now_reading'])
def now_reading_handler(message):
    try:
        bot.reply_to(message, "now_reading")
    except Exception as e:
        bot.reply_to(message, f"⚠️ Ошибка: {str(e)}")

@bot.message_handler(commands=['poem_mode'])
def poem_mode_handler(message):
    try:
        bot.reply_to(message, "poem_mode")
    except Exception as e:
        bot.reply_to(message, f"⚠️ Ошибка: {str(e)}")

@bot.message_handler(content_types=['document'])
def handle_document(message):
    try:
        bot.reply_to(message, "document")
    except Exception as e:
        bot.reply_to(message, f"⚠️ Ошибка: {str(e)}")

@bot.message_handler(content_types=['text'])
def handle_text(message):
    try:
        chat_id = message.chat.id
        bot.reply_to(message, "privet-privet")

    except Exception as e:
        bot.reply_to(message, f"⚠️ Ошибка: {str(e)}")