import os
from text_transliter import *


class FileExtractor(object):
    """file from user which has been sent in bot"""

    def __init__(self):
        self.tt = TextTransliter()
        pass

    def _get_file_user_sent(self, telebot, message):
        # get file and filename which have been sent by user in bot
        file_info = telebot.get_file(message.document.file_id)
        downloaded_file = telebot.download_file(file_info.file_path)
        filename = self.tt.translite_text(message.document.file_name)
        return downloaded_file, filename

    def local_save_file(self, telebot, message, download_path):
        # save file from user to local folder
        downloaded_file, filename = self._get_file_user_sent(telebot, message)
        
        print(f"📁 Путь для сохранения: {download_path}")
        print(f"📄 Имя файла: {filename}")
        
        # Создаем директорию, если она не существует
        os.makedirs(download_path, exist_ok=True)
        print(f"📂 Директория создана/проверена: {download_path}")
        
        # todo make it throw regex, ept
        if (filename.find('.epub') != -1):
            # file_from_user = save_file(downloaded_file, path_for_save, filename)
            path_for_save = os.path.join(download_path, filename)
            print(f"💾 Сохраняем файл по пути: {path_for_save}")
            with open(path_for_save, 'wb') as new_file:
                new_file.write(downloaded_file)
            print(f"✅ Файл успешно сохранен: {path_for_save}")
            return path_for_save
        else:
            print(f"❌ Неподдерживаемый тип файла: {filename}")
            return -1  # type error
