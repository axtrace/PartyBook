import re

class TextReplacer(object):
    """replace texts"""

    def __init__(self):
        pass
    def text_re_substitute(self, text, replace_dict):
        # replace in text all dict key to dict[key] as patterns for re.sub
        result_text = text
        for key in replace_dict:
            pattern_from = key
            pattern_to = replace_dict[key]
            result_text = re.sub(pattern_from, pattern_to, result_text)
        return result_text

    def text_replace(self, text, replace_dict):
        # replace in text all dict keys to dict[key] value
        result_text = text
        for key in replace_dict:
            text_from = str(key)
            text_to = str(replace_dict[key])
            result_text = result_text.replace(text_from, text_to)
        return result_text

if __name__ == '__main__':
    tr = TextReplacer()

    tdict = {'pp':'vvvv',
             "'":'"',
             'b"': '"',
             '\n': '',
             'False': 'false',
             'True': 'true'
    }

    re_dict = {r'(\w+):': r'"\1":'}
    text = "property: false"
    print(tr.text_replace(text, tdict))
    print(tr.text_re_substitute(text, re_dict))
