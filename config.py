import os

path_for_save = os.path.join(os.getcwd(),
                             'files')  # path for saving files
piece_size = 384  # 384 get approximately, for comfortable reading on smartphone

message_hello = '''
Hello! It seems you are a new user! Glad to see you! 
Please send me .epub file for start reading. 
I will notify you with a little piece of text every day at 20:20. 
You can stop auto-notification by command /stop_auto
For more info use /help
'''

success_start_reply = '''
Let\'s start. 
For continue reading use command /more. 
For upload book send .epub file
For more info use /help
'''

success_file_added = '''
Success! File added. 
For start reading use command /more
For more info use /help
'''

error_file_type = 'Error! Only .epub files allowed'
error_file_adding_failed = 'Error! I failed with saving file. Try again'
error_current_book = 'I do not know your current book'
error_book_recognition = '''

Error! I do not recognize this book name. 
Choose one from /my_books
For more info use /help
'''

error_user_finding = 'Sorry, did not find you in users. Try command /start'

message_everyday_ON = 'Everyday auto send is ON. /stop_auto'

message_everyday_OFF = 'Everyday auto send is OFF. /start_auto'

message_help = '''
I am bot for reading books.
You can send me .epub file and start reading it.
I will notify you with a little piece of text every day at 20:20. 
You can request next a piece of text by command /more
You can stop auto-notification at any moment by command /stop_auto
For upload a poem book use command /poem_mode
Other available commands are on the keyboard under text field.
Good luck!
'''
message_poem_mode_ON = 'Poem mode is ON. Please send a book file'
message_poem_mode_OFF = 'Poem mode is OFF. Please send a book file'  # todo: implement it

message_dont_understand = 'I do not understand {}. \nSee commands at /help'
message_now_reading = 'Now you are reading: {}. /more'
message_booklist = 'Your books list: ' + '\n'
message_choose_book = '------\n' + 'Choose the book for start reading'
