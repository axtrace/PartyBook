import json
import sys
import os
from .ydb_adapter import YdbAdapter
from .text_replacer import TextReplacer


class DbManager:
    """interaction with DB, preparing requests and sending to execute"""

    def __init__(self):
        self.db_adapter = YdbAdapter()
        self.text_replacer = TextReplacer()

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

    def _execute_safe_query(self, query, params=None):
        """
        Безопасное выполнение запроса с параметрами
        """
        if params:
            # Заменяем параметры в запросе
            for key, value in params.items():
                if isinstance(value, str):
                    value = value.replace('"', '\\"')
                query = query.replace(f"{{{key}}}", str(value))
        
        try:
            result = self.db_adapter.execute_query(query)
            return result
        except Exception as e:
            print(f"Error executing query: {str(e)}")
            return None

    def update_book_pos(self, user_id, book_id, newpos):
        query = """
            UPDATE user_books
            SET pos = {newpos}
            WHERE userId = {user_id} AND bookId = {book_id};
        """
        return self._execute_safe_query(query, {
            'user_id': user_id,
            'book_id': book_id,
            'newpos': newpos
        })

    def update_current_book(self, user_id, book_id):
        # Деактивируем предыдущую активную книгу пользователя
        deactivate_query = f"""
            UPDATE user_books
            SET isActive = false
            WHERE userId = {user_id} AND isActive = true;
        """
        self.db_adapter.execute_query(deactivate_query)

        # Активируем новую книгу
        activate_query = f"""
            UPSERT INTO user_books
                (userId, bookId, isActive)
            VALUES
                ({user_id}, {book_id}, true);
        """
        self.db_adapter.execute_query(activate_query)
        return 0

    def update_auto_status(self, user_id, status_to):
        # change status of auto-sending
        new_status = self.bool_to_str(status_to)
        query = f"""
            UPSERT INTO users
                (userId, isAutoSend)
            VALUES
                ({user_id}, {new_status});
        """
        self.db_adapter.execute_query(query)
        return 0

    def update_user_lang(self, user_id, lang):
        # change lang for user
        query = f"""
            UPSERT INTO users
                (userId,lang)
            VALUES
                ({user_id},"{lang}");
        """
        self.db_adapter.execute_query(query)
        return 0

    def get_current_book(self, user_id):
        # todo: переделать на параметризованный запрос (везде)
        query = """
            SELECT ub.bookId, b.bookname, ub.pos, ub.mode 
            FROM user_books ub
            JOIN books b ON ub.bookId = b.id
            WHERE ub.userId = {user_id} 
            AND ub.isActive = true;
        """
        result = self._execute_safe_query(query, {'user_id': user_id})
        if not result or len(result[0].rows) == 0:
            return None, None, None
        data = self._text_to_json(str(result[0].rows[0]))
        # todo: перед возвратом сделать модель Book
        return data['bookId'], data['bookname'], data['pos'], data['mode']

    def get_auto_status(self, user_id):
        # return status of auto-sending
        query = f"""
            SELECT isAutoSend FROM users
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
            FROM user_books ub
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
            SELECT userId FROM users
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
            SELECT bookId, pos FROM user_books
            WHERE userId = {user_id} AND bookId = {book_id};
        """
        result = self.db_adapter.execute_query(query)
        if len(result[0].rows) == 1:
            data = self._text_to_json(str(result[0].rows[0]))
            book_id = data['bookId']
            book_pos = data['pos']
            return book_id, book_pos
        return -1


    def get_user_lang(self, user_id):
        # Return lang for user
        query = f"""
            SELECT lang FROM users
            WHERE userId = {user_id};
        """

        result = self.db_adapter.execute_query(query)

        if len(result[0].rows) == 1:
            data = self._text_to_json(str(result[0].rows[0]))
            lang = data['lang']
            return lang
        return None

    def save_chunk(self, book_id, chunk_id, text):
        query = f"""
            UPSERT INTO book_chunks
                (bookId, chunkId, text)
            VALUES
            ({book_id}, {chunk_id}, "{text}");
        """
        self.db_adapter.execute_query(query)
        return 0

    def get_chunk(self, book_id, chunk_id):
        query = """
            SELECT text FROM book_chunks
            WHERE bookId = {book_id} AND chunkId = {chunk_id};
        """
        result = self._execute_safe_query(query, {
            'book_id': book_id,
            'chunk_id': chunk_id
        })
        if not result or len(result[0].rows) == 0:
            return None
        data = self._text_to_json(str(result[0].rows[0]))
        return data['text']

    def get_total_chunks(self, book_id):
        query = f"""
            SELECT COUNT(*) as count FROM book_chunks
            WHERE bookId = {book_id};
        """
        result = self.db_adapter.execute_query(query)
        if len(result[0].rows) == 0:
            return 0
        data = self._text_to_json(str(result[0].rows[0]))
        return data['count']

    def get_or_create_book(self, book_name):
        query = f"""
            UPSERT INTO books
                (bookname)
            VALUES
            ("{book_name}")
            RETURNING id;
        """
        result = self.db_adapter.execute_query(query)
        data = self._text_to_json(str(result[0].rows[0]))
        return data['id']
