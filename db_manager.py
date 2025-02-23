import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import ydb_adapter
import text_replacer


class DbManager:
    """interaction with DB, preparing requests and sending to execute"""

    def __init__(self):
        self.db_adapter = ydb_adapter.YdbAdapter()
        self.text_replacer = text_replacer.TextReplacer()

    def _text_to_json(self, text):
        if not isinstance(text, str):
            return text

        text_dict = {
                 "'": '"',
                 'b"': '"',
                 '\n': '',
                 'False': 'false',
                 'True': 'true'
        }
        re_dict = {r'(\w+):': r'"\1":'}
        text = self.text_replacer.text_replace(text, text_dict)
        text = self.text_replacer.text_re_substitute(text, re_dict)

        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}\nProblematic text: {text}")
            return None

    def str_to_bool(self, value):
        return value.lower() in ('true', 't', 'yes', 'y', '1')

    def bool_to_str(self, value):
        return str(value).lower()

    def update_book_pos(self, user_id, book_id, newpos):
        # Update pos value for user and book
        # to-do: think about DECLARE $userId AS Int64; DECLARE $userName AS Utf8;
        query = f"""
            UPDATE user_books_test
            SET pos={newpos}
            WHERE userId={user_id} AND bookId={book_id};
        """
        self.db_adapter.execute_query(query)
        return 0

    def update_current_book(self, user_id, book_id):
        # Update book currently reading by user
        query = f"""
            UPSERT INTO user_books_test
                (userId, bookId, isActive)
            VALUES
            ({user_id}, {book_id}, true);
        """
        self.db_adapter.execute_query(query)
        return 0

    def update_auto_status(self, user_id, status_to):
        # change status of auto-sending
        new_status = self.bool_to_str(status_to)
        query = f"""
            UPSERT INTO users_test
                (userId, isAutoSend)
            VALUES
                ({user_id}, {new_status});
        """
        self.db_adapter.execute_query(query)
        return 0

    def update_user_lang(self, user_id, lang):
        # change lang for user
        query = f"""
            UPSERT INTO users_test
                (userId,lang)
            VALUES
                ({user_id},"{lang}");
        """
        self.db_adapter.execute_query(query)
        return 0

    def get_current_book(self, user_id):
        # get current book of user
        query = f"""
            SELECT ub.bookId as bookId, ub.pos as pos, bt.bookname as bookname
            FROM user_books_test ub
            JOIN books_test bt ON ub.bookId = bt.id
            WHERE ub.userId = {user_id} AND isActive = true;
        """
        result = self.db_adapter.execute_query(query)

        if len(result[0].rows) == 1:
            data = self._text_to_json(str(result[0].rows[0]))
            book_id = data['bookId']
            book_name = data['bookname']
            pos = data['pos']
            return book_id, book_name, pos
        return None, None, None
        # пример значения:
        # "body": "{'bookId': 4, 'pos': 1482}\n"


    def get_auto_status(self, user_id):
        # return status of auto-sending
        query = f"""
            SELECT isAutoSend FROM users_test
            WHERE userId = {user_id};
        """
        result = self.db_adapter.execute_query(query)
        if len(result[0].rows) == 1:
            data = self._text_to_json(str(result[0].rows[0]))
            status = self.str_to_bool(data['isAutoSend'])
            return status
        return -1

    def get_user_books(self, user_id):
        # Return all user's books
        query = f"""
            SELECT ub.bookId as bookId, bt.bookname as bookname
            FROM user_books_test ub
            JOIN books_test bt ON ub.bookId = bt.id
            WHERE ub.userId = {user_id};
        """

        result = self.db_adapter.execute_query(query)

        user_books = []

        for row in result[0].rows:
            data = self._text_to_json(str(row[0]))
            book_id = data['bookId']
            book_name = data['bookname']
            user_books.append({book_id: book_name})

        return user_books

    def get_users_for_autosend(self):
        # Return all user with auto-sending ON

        query = f"""
            SELECT userId FROM users_test
            WHERE isAutoSend = true;
        """
        result = self.db_adapter.execute_query(query)

        user_ids = []

        for row in result[0].rows:
            data = self._text_to_json(row)
            user_id = data['userId']
            user_ids.append(user_id)

        return user_ids

    def get_book_pos(self, user_id, book_id):
        # Return pos value for user and book
        # def get_pos(self, user_id, book_name):
        query = f"""
            SELECT bookId, pos FROM user_books_test
            WHERE userId = {user_id} AND bookId = {book_id};
        """
        result = self.db_adapter.execute_query(query)
        if len(result[0].rows) == 1:
            data = self._text_to_json(str(result[0].rows[0]))
            book_id = data['bookId']
            pos = data['pos']
            return book_id, pos
        return -1


    def get_user_lang(self, user_id):
        # Return lang for user
        query = f"""
            SELECT lang FROM users_test
            WHERE userId = {user_id};
        """

        result = self.db_adapter.execute_query(query)

        if len(result[0].rows) == 1:
            data = self._text_to_json(str(result[0].rows[0]))
            lang = data['lang']
            return lang
        return None
