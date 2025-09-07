import errno
from transliterate import translit, get_available_language_codes
from langdetect import detect


class TextTransliter(object):
    # convert text from one alphabet to other.

    def __init__(self):
       pass

    def _transliterate(self, text, lang_from):
        # convert from russian to translit
        try:
            if lang_from == '':
                lang_from = detect(text)
            if lang_from not in get_available_language_codes():
                lang_from = 'ru'
            return translit(text, lang_from, reversed=True)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise
        pass

    def translite_text(self, text, lang_from = ''):
        return self._transliterate(text, lang_from)
