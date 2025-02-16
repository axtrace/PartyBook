import sqlite3
import json

import os
import ydb
import ydb.iam


class DbManager:
    """work with DataBase"""

    def __init__(self):
        # Create driver in global space.
        driver = ydb.Driver(
            endpoint=os.getenv('YDB_ENDPOINT'),
            database=os.getenv('YDB_DATABASE'),
            credentials=ydb.iam.MetadataUrlCredentials()
        )

        # Wait for the driver to become active for requests.

        driver.wait(fail_fast=True, timeout=5)

        # Create the session pool instance to manage YDB sessions.
        self.pool = ydb.SessionPool(driver)

    def _run_transaction(self, session, query):
        # Create the transaction and execute query.
        return session.transaction().execute(
            query,
            commit_tx=True,
            settings=ydb.BaseRequestSettings().with_timeout(3).with_operation_timeout(2)
        )

    def execute_query(self, query):
        result = self.pool.retry_operation_sync(
            lambda session: self._run_transaction(session, query))
        return result

    def _text_to_json(self, text):
        body = text.strip().replace("'", '"')
        body = body.replace('\n', '')
        body = body.replace('False', 'false').replace('True', 'true')
        json_data = json.loads(body)
        return json_data


    def update_book_pos(self, user_id, book_id, newpos):
        # Update pos value for user and book
        # to-do: think about DECLARE $userId AS Int64; DECLARE $userName AS Utf8;
        query = f"""
            UPDATE user_books_test
            SET pos={newpos}
            WHERE
                userId={user_id}
                AND bookId={book_id}
            ;
        """
        self.execute_query(query)
        return 0

    def update_current_book(self, user_id, book_id):
        # Update book currently reading by user
        query = f"""
            UPSERT INTO user_books_test
            (
                userId,
                bookId,
                isActive
            )
            VALUES
            (
                {user_id},
                {book_id},
                true
            )
        ;"""
        self.execute_query(query)
        return 0

    def update_auto_status(self, user_id):
        # change status of auto-sending
        query = f"""
            UPSERT INTO users_test
            (
                userId,
                isAutoSend
            )
            VALUES
            (
                {user_id},
                true
        );"""
        self.execute_query(query)
        return 0

    def update_lang(self, user_id, lang):
        # change lang for user
        query = f"""
            UPSERT INTO users_test
            (
                userId,
                lang
            )
            VALUES
            (
                {user_id},
                {lang}
        );"""
        self.execute_query(query)
        return 0

    def get_current_book(self, user_id):
        # get current book of user
        query = f"""
            SELECT bookId, pos FROM user_books_test
            WHERE userId = {user_id} AND isActive = true
        ;"""
        result = self.execute_query(query)
        if len(result[0].rows) == 1:
            data = self._text_to_json(str(result[0].rows[0]))
            book_id = data['bookId']
            pos = data['pos']
            return book_id, pos
        return None
        # пример значения:
        # "body": "{'bookId': 4, 'pos': 1482}\n"


    def get_auto_status(self, user_id):
        # return status of auto-sending
        query = f"""
            SELECT isAutoSend FROM users_test
            WHERE userId = {user_id}
        ;
        """
        result = self.execute_query(query)
        if len(result[0].rows) == 1:
            data = self._text_to_json(str(result[0].rows[0]))
            return data['isAutoSend']
        return -1

    def get_user_books(self, user_id):
        # Return all user's books
        query = f"""
            SELECT bookId FROM user_books_test
            WHERE userId = {user_id}
        ;"""

        result = self.execute_query(query)

        user_book_ids = []

        for row in result[0].rows:
            data = self._text_to_json(str(result[0].rows[0]))
            book_id = data['bookId']
            user_book_ids.append(book_id)

        return user_book_ids

    def get_users_for_autosend(self):
        # Return all user with auto-sending ON

        query = """
        SELECT userId FROM users_test
        WHERE isAutoSend = true
        ;
        """
        result = execute_query(query)

        user_ids = []

        for row in result[0].rows:
            data = text_to_json(str(result[0].rows[0]))
            user_id = data['userId']
            user_ids.append(user_id)

        return user_book_ids

    def get_pos(self, user_id, book_id):
        # Return pos value for user and book
        # def get_pos(self, user_id, book_name):
        query = f"""
            SELECT bookId, pos FROM user_books_test
            WHERE userId = {user_id} AND bookId = book_id
        ;"""
        result = self.execute_query(query)
        if len(result[0].rows) == 1:
            data = self._text_to_json(str(result[0].rows[0]))
            book_id = data['bookId']
            pos = data['pos']
            return book_id, pos
        return -1


    def get_lang(self, user_id):
        # Return lang for user
        query = f"""
            SELECT lang FROM users_test
            WHERE userId = {user_id}
        ;"""

        result = self.execute_query(query)

        if len(result[0].rows) == 1:
            data = self._text_to_json(str(result[0].rows[0]))
            lang = data['lang']
            return lang
        return None
