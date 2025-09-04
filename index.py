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

# Список команд для клавиатуры
commands = ['/help', '/more', '/my_books', '/auto_status', '/now_reading',
            '/poem_mode', '/change_lang']

def markup(clist):
    if len(clist) == 0:
        return telebot.types.ReplyKeyboardRemove(True)
    user_markup = telebot.types.ReplyKeyboardMarkup(True,
                                                    one_time_keyboard=True)
    for item in clist:
        user_markup.row(item)
    return user_markup

# Создаем основную клавиатуру
user_markup_normal = markup(commands)

def handler(event, context):
    message = telebot.types.Update.de_json(event['body'])
    bot.process_new_updates([message])
    return {
        'statusCode': 200,
        'body': 'OK'
    }

@bot.message_handler(commands=['start'])
def start_handler(message):
    try:
        bot.reply_to(message, "start", reply_markup=user_markup_normal)
    except Exception as e:
        bot.reply_to(message, f"⚠️ Ошибка: {str(e)}")

@bot.message_handler(commands=['more'])
def more_handler(message):
    try:
        bot.reply_to(message, "more", reply_markup=user_markup_normal)
    except Exception as e:
        bot.reply_to(message, f"⚠️ Ошибка: {str(e)}")

@bot.message_handler(commands=['help'])
def help_handler(message):
    try:
        bot.reply_to(message, "help", reply_markup=user_markup_normal)
    except Exception as e:
        bot.reply_to(message, f"⚠️ Ошибка: {str(e)}")

@bot.message_handler(commands=['my_books'])
def my_books_handler(message):
    try:
        bot.reply_to(message, "my_books", reply_markup=user_markup_normal)
    except Exception as e:
        bot.reply_to(message, f"⚠️ Ошибка: {str(e)}")

@bot.message_handler(commands=['auto_status'])
def auto_status_handler(message):
    try:
        bot.reply_to(message, "auto_status", reply_markup=user_markup_normal)
    except Exception as e:
        bot.reply_to(message, f"⚠️ Ошибка: {str(e)}")

@bot.message_handler(commands=['now_reading'])
def now_reading_handler(message):
    try:
        bot.reply_to(message, "now_reading", reply_markup=user_markup_normal)
    except Exception as e:
        bot.reply_to(message, f"⚠️ Ошибка: {str(e)}")

@bot.message_handler(commands=['poem_mode'])
def poem_mode_handler(message):
    try:
        bot.reply_to(message, "poem_mode", reply_markup=user_markup_normal)
    except Exception as e:
        bot.reply_to(message, f"⚠️ Ошибка: {str(e)}")

@bot.message_handler(commands=['change_lang'])
def change_lang_handler(message):
    try:
        bot.reply_to(message, "change_lang", reply_markup=user_markup_normal)
    except Exception as e:
        bot.reply_to(message, f"⚠️ Ошибка: {str(e)}")

@bot.message_handler(commands=['stop_auto', 'start_auto'])
def auto_control_handler(message):
    try:
        bot.reply_to(message, "auto_control", reply_markup=user_markup_normal)
    except Exception as e:
        bot.reply_to(message, f"⚠️ Ошибка: {str(e)}")

@bot.message_handler(content_types=['document'])
def handle_document(message):
    try:
        bot.reply_to(message, "document", reply_markup=user_markup_normal)
    except Exception as e:
        bot.reply_to(message, f"⚠️ Ошибка: {str(e)}")

@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_text(message):
    try:
        bot.reply_to(message, "privet-privet", reply_markup=user_markup_normal)
    except Exception as e:
        bot.reply_to(message, f"⚠️ Ошибка: {str(e)}")