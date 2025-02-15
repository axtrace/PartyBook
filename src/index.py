import telebot
from telebot import types
import json
import os
import requests
from bs4 import BeautifulSoup


# Telegram Access
token = os.environ['TEST_TOKEN']
bot = telebot.TeleBot(token, threaded=False)


# Cloud Function Handler
def handler(event,context):
    print(event)
    body = json.loads(event['body'])
    update = telebot.types.Update.de_json(body)
    bot.process_new_updates([update])


# Start
@bot.message_handler(commands=['start'])
def start_helper(message):
    bot.reply_to(message, "Привет! Отправь мне трек-номер посылки, и я проверю ее статус.")


# Default Reply
@bot.message_handler(content_types=["text"])
def repeat_all_messages(message):
    bot.send_message(message.chat.id, "Не понял команды")

