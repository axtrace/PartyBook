import re
import errno
from nltk.tokenize import sent_tokenize


class TextSeparator(object):
    """Split text to sentenses, the way depence on mode value
    If the mode is by_sense, bot try to make sentenses even if they finished without a dot
    Else the bot make sentenses just only by newline simbols"""
    _input_text = ''
    _output_sentenses = []

    def __init__(self, in_text='', mode=''):
        """Constructor"""
        try:
            self._input_text = in_text
            self._spit_text_to_sensenses(mode=mode)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

    def get_sentenses(self):
        return self._output_sentenses

    def _spit_text_to_sensenses(self, mode):
        text = self._input_text
        if mode == 'by_sense':
            # replace [letter or digit] + newline + big letter after --> '. '
            spec_regex = r'\w[\n\r\f\v]+[0-9A-ZА-Я]'
            text = re.sub(spec_regex, self._dashrepl, text, flags=re.M)
            # make one big string from all textlines and then seperate them by dot
            text = re.sub(r'\s+', ' ', text, flags=re.M)
        self._output_sentenses = sent_tokenize(text, 'russian')  # todo: auto detect lang

    def _dashrepl(self, matchobj):
        # replace newstring to '. '
        textpeace = matchobj.group(0)
        return re.sub(r'[\n\r\f\v]+', '. ', textpeace, flags=re.M)

    def _print(self):
        for sent in self._output_sentenses:
            print(sent)


if __name__ == '__main__':
    input_file = open('input.txt', 'r', encoding='utf-8')
    text = input_file.read()
    ts1 = TextSeparator(text)
    ts2 = TextSeparator(text, mode='by_sense')
    ts1._print()
    ts2._print()
