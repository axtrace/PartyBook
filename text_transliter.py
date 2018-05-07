import errno
from transliterate import translit, get_available_language_codes
from langdetect import detect


class TextTransliter(object):
    _input_text = ''
    _output_text = ''

    def __init__(self, input_text=''):
        try:
            self._input_text = input_text
            self._transliterate()
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

    def _transliterate(self):
        # convert from russian to translit
        try:
            input_lang = detect(self._input_text)
            if input_lang not in get_available_language_codes:
                input_lang = 'ru'
            self._output_text = translit(self._input_text, input_lang, reversed=True)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

    def get_translitet(self):
        return self._output_text


if __name__ == '__main__':
    rus_str = '123 Медлячок, чтобы ты заплакала'

    tt = TextTransliter(rus_str)
    print(tt.get_translitet())
