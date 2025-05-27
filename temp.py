from nltk.tokenize import sent_tokenize

text = "Это первое предложение. Это второе предложение. А это третье."

import nltk
nltk.download('punkt')



import ssl
import nltk
nltk.download('punkt', download_dir='./nltk_data',
              ssl_context=ssl.create_default_context(cafile=certifi.where()))


# print(sent_tokenize(text))
