import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src import db_manager

dbm = db_manager.DbManager()

user_id = 2505806
book_id = 190
newpos = 2020


print(dbm.update_book_pos(user_id, book_id, newpos))
print(dbm.update_current_book(user_id,book_id))
print(dbm.update_auto_status(user_id, 'true'))
print(dbm.update_user_lang(user_id, r"fr"))
print(dbm.get_current_book(user_id))
print(dbm.get_auto_status(user_id))
print(dbm.get_user_books(user_id))
print(dbm.get_users_for_autosend())
print(dbm.get_book_pos(user_id, book_id))
print(dbm.get_user_lang(user_id))