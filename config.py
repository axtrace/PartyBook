import os
import json

f = open("config.json", "r", encoding='utf-8')
cfg = json.loads(f.read())

path_for_save = os.path.join(os.getcwd(), 'files')  # path for saving files
piece_size = 500  # 384 get approximately, for comfortable reading on smartphone

end_book_string = '---THE END---'

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

error_file_type = cfg.get('error_file_type', '')
error_file_adding_failed = cfg.get('error_file_adding_failed', '')
error_current_book = cfg.get('error_current_book', '')
error_book_recognition = cfg.get('error_book_recognition', '')
error_user_finding = cfg.get('error_user_finding', '')
error_lang_recognition = cfg.get('error_lang_recognition', '')
