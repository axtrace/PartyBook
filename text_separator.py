import re
import errno
from nltk.tokenize import sent_tokenize


class TextSeparator(object):
    """Split text to sentences, the way depends on mode value
    If the mode is by_sense, bot try to make sentences even if they finished without a dot
    Else the bot make sentences just only by newline symbols"""

    def __init__(self, in_text='', mode=''):
        """Constructor"""
        try:
            self._input_text = in_text
            self._spit_text_to_sensenses(mode=mode)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise
        pass

    def get_sentences(self):
        return self._output_sentences

    def _spit_text_to_sensenses(self, mode):
        text = self._input_text
        spec_regex = r'\w[\n\r\f\v]+[0-9A-ZА-Я]'
        if mode == 'by_sense':
            # replace [letter or digit] + newline + big letter after --> '. '
            text = re.sub(spec_regex, self._dashrepl, text, flags=re.M)
            # make one big string from all textlines and then separate them by dot
            text = re.sub(r'\s+', ' ', text, flags=re.M)
            self._output_sentences = sent_tokenize(text, 'russian')  # todo: auto detect lang
        else:
            self._output_sentences = text.split(sep='\n')
        pass

    def _dashrepl(self, matchobj):
        # replace newstring to '. '
        text_piace = matchobj.group(0)
        return re.sub(r'[\n\r\f\v]+', '. ', text_piace, flags=re.M)

    def _print(self):
        for sent in self._output_sentences:
            print(sent)
        pass


if __name__ == '__main__':
    input_file = open('input.txt', 'r', encoding='utf-8')
    text = input_file.read()
    ts1 = TextSeparator(text)
    ts2 = TextSeparator(text, mode='by_sense')
    ts1._print()
    print('----------')
    ts2._print()
