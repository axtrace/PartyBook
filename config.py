import os

path_for_save = os.path.join(os.getcwd(),
                             'files')  # path for saving files
peaceSize = 384  # 384 get approximately, for comfortable reading on smartphone

new_user_hello = '''
Hello! It seems you are new user! Glad to see you! 
Please send me .epub file for start reading. 
I will notify you with a little peace of text everyday at 20:20. 
You can stop auto-notification by command /stop_auto
For more info use /help
'''

startReply = '''
Let\'s start. 
For continue reading use command /more. 
For upload book send .epub file
For more info use /help
'''

fileAddReply = '''
Success! File added. 
For start reading use command /more
For more info use /help
'''

fileAddErrorType = 'Error! Only .epub files allowed'
fileAddErrorFailed = 'Error! I failed with saving file. Try again'

bookRecognError = '''
Error! I do not recognised this bookname. 
Choose one from /my_books
For more info use /help
'''

noUserFoundErr = 'Sorry, did not find you in users. Try command /start'

everyday_ON = 'Everyday auto send is ON. /stop_auto'

everyday_OFF = 'Everyday auto send is OFF. /start_auto'

help_text = '''
I am bot for reading books.
You can send me .epub file and start read it.
I will notify you with a little peace of text everyday at 20:20. 
You cab request next a peace of text by command /more
You can stop auto-notification at any moment by command /stop_auto
Other available commands are on keyboard under text field.
Good luck!
'''
