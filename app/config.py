import os
import json

# Ищем config.json относительно расположения config.py
config_path = os.path.join(os.path.dirname(__file__), "config.json")

try:
    with open(config_path, "r", encoding='utf-8') as f:
        cfg = json.loads(f.read())
except FileNotFoundError:
    print(f"Warning: config.json not found at {config_path}")
    # Fallback значения по умолчанию
    cfg = {
        "message_success_start": {
            "ru": "Привет! Я бот для чтения книг.",
            "en": "Hello! I am a book reading bot."
        },
        "message_file_added": {
            "ru": "Файл успешно добавлен!",
            "en": "File added successfully!"
        },
        "error_file_type": {
            "ru": "Ошибка! Принимаю только файлы .epub",
            "en": "Error! Only .epub files allowed"
        },
        "error_file_processing": {
            "ru": "Извините, произошла ошибка при обработке файла. Попробуйте еще раз.",
            "en": "Sorry, an error occurred while processing the file. Please try again."
        },
        "error_file_adding_failed": {
            "ru": "Ошибка! Не удалось сохранить файл.",
            "en": "Error! Failed to save file."
        },
        "error_current_book": {
            "ru": "Я не знаю такой книги",
            "en": "I do not know your current book"
        },
        "error_book_recognition": {
            "ru": "Ошибка! Я не распознал имя книги.",
            "en": "Error! I do not recognize this book name."
        },
        "error_user_finding": {
            "ru": "Извините, не узнаю вас. Начните с команды /start",
            "en": "Sorry, did not find you. Try command /start"
        },
        "error_lang_recognition": {
            "ru": "Извините, такой язык недоступен.",
            "en": "Sorry, did not recognize this language."
        },
        "message_everyday_ON": {
            "ru": "Ежедневная рассылка включена.",
            "en": "Everyday auto send is ON."
        },
        "message_everyday_OFF": {
            "ru": "Ежедневная рассылка выключена.",
            "en": "Everyday auto send is OFF."
        },
        "message_poem_mode_ON": {
            "ru": "Режим стихов включен.",
            "en": "Poem mode is ON."
        },
        "message_poem_mode_OFF": {
            "ru": "Режим стихов выключен.",
            "en": "Poem mode is OFF."
        },
        "message_book_finished": {
            "ru": "Поздравляю! Книга окончена.",
            "en": "Congratulations! The book is finished."
        },
        "message_dont_understand": {
            "ru": "Я не понял команду.",
            "en": "I do not understand this command."
        },
        "message_lang_changed": {
            "ru": "Язык успешно изменен.",
            "en": "Language has been changed."
        },
        "message_now_reading": {
            "ru": "Сейчас вы читаете: {}.",
            "en": "Now you are reading: {}."
        },
        "message_booklist": {
            "ru": "Список ваших книг:",
            "en": "Your books list:"
        },
        "message_choose_book": {
            "ru": "Выберите книгу для чтения",
            "en": "Choose the book for start reading"
        },
        "message_help": {
            "ru": "Я бот для чтения книг. Используйте /more для чтения.",
            "en": "I am bot for reading books. Use /more to read."
        },
        "message_empty_booklist": {
            "ru": "Список книг пуст",
            "en": "Your book list is empty"
        }
    }

path_for_save = os.path.join(os.getcwd(), 'files')  # path for saving files
piece_size = 893  # 384 get approximately, for comfortable reading on smartphone
max_msg_size = 4096 # restriction from telegram

end_book_string = '---THE END---'

# Создаем объект config для совместимости с импортом
class Config:
    def __init__(self, cfg_dict):
        for key, value in cfg_dict.items():
            setattr(self, key, value)
    
    def get(self, key, default=None):
        return getattr(self, key, default)

# Создаем экземпляр config
config = Config(cfg)

message_file_added = cfg.get('message_file_added', '')
message_success_start = cfg.get('message_success_start', '')
message_everyday_ON = cfg.get('message_everyday_ON', '')
message_everyday_OFF = cfg.get('message_everyday_OFF', '')
message_help = cfg.get('message_help', '')
message_poem_mode_ON = cfg.get('message_poem_mode_ON', '')
message_poem_mode_OFF = cfg.get('message_poem_mode_OFF', '')
message_book_finished = cfg.get('message_book_finished', '')
message_dont_understand = cfg.get('message_dont_understand', '')
message_now_reading = cfg.get('message_now_reading', '')
message_booklist = cfg.get('message_booklist', '')
message_choose_book = cfg.get('message_choose_book', '')
message_lang_changed = cfg.get('message_lang_changed', '')
message_empty_booklist = cfg.get('message_empty_booklist', '')

error_file_type = cfg.get('error_file_type', '')
error_file_processing = cfg.get('error_file_processing', '')
error_file_adding_failed = cfg.get('error_file_adding_failed', '')
error_current_book = cfg.get('error_current_book', '')
error_book_recognition = cfg.get('error_book_recognition', '')
error_user_finding = cfg.get('error_user_finding', '')
error_lang_recognition = cfg.get('error_lang_recognition', '')

webhook_port = 8443  # 443, 80, 88 or 8443 (port need to be 'open')
webhook_listen = '0.0.0.0'

webhook_ssl_cert = './webhook_cert.pem'  # Path to the ssl certificate
webhook_ssl_priv = './webhook_pkey.pem'  # Path to the ssl private key
