import json
import re
import ast
import sys
import os
from ydb_adapter import YdbAdapter
from text_replacer import TextReplacer


class DbManager:
    """interaction with DB, preparing requests and sending to execute"""

    def __init__(self):
        self.db_adapter = YdbAdapter()
        self.text_replacer = TextReplacer()

    def _text_to_json(self, text):
        if not isinstance(text, str):
            print(f"❌ Ошибка: ожидалась строка, получен {type(text)}")
            return None

        # Проверяем, если это уже Python словарь (repr format)
        if text.startswith('{') and text.endswith('}'):
            try:
                # Пытаемся распарсить как Python литерал
                result = ast.literal_eval(text)
                # Обрабатываем bytes объекты в результате
                if isinstance(result, dict):
                    processed_result = {}
                    for key, value in result.items():
                        if isinstance(value, bytes):
                            # Декодируем bytes в строку
                            processed_result[key] = value.decode('utf-8', errors='ignore')
                        else:
                            processed_result[key] = value
                    return processed_result
                return result
            except (ValueError, SyntaxError) as e:
                print(f"❌ Ошибка парсинга Python литерала: {e}")
                pass

        # Универсальный подход - обрабатываем все проблемные символы пошагово
        
        # 1. Сначала экранируем все кавычки в строковых значениях
        # Ищем паттерн: "key": "value"with"quotes"inside"
        # Заменяем на: "key": "value\"with\"quotes\"inside"
        
        def fix_quotes_in_strings(match):
            key = match.group(1)
            value = match.group(2)
            # Экранируем все кавычки внутри значения
            escaped_value = value.replace('"', '\\"')
            return f'"{key}": "{escaped_value}"'
        
        # Ищем строки вида: "key": "value"with"quotes"
        fixed_text = re.sub(r'"([^"]+)":\s*"([^"]*)"([^"]*)"', fix_quotes_in_strings, text)
        
        # 2. Экранируем контрольные символы
        fixed_text = fixed_text.replace('\n', '\\n')
        fixed_text = fixed_text.replace('\r', '\\r')
        fixed_text = fixed_text.replace('\t', '\\t')
        fixed_text = fixed_text.replace('\x00', '\\u0000')
        
        # 3. Обрабатываем остальные замены
        fixed_text = fixed_text.replace("'", '"')
        fixed_text = fixed_text.replace('True', 'true')
        fixed_text = fixed_text.replace('False', 'false')
        fixed_text = fixed_text.replace('None', 'null')

        # 4. Добавляем кавычки вокруг ключей, если они не заключены в кавычки
        fixed_text = re.sub(r'([a-zA-Z_][a-zA-Z0-9_.]*):', r'"\1":', fixed_text)

        try:
            return json.loads(fixed_text)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            print(f"Problematic text: {text}")
            print(f"Fixed text: {fixed_text}")
            
            # Fallback к ast.literal_eval если JSON парсинг не удался
            try:
                ast_text = fixed_text.replace('"', "'")
                return ast.literal_eval(ast_text)
            except (ValueError, SyntaxError) as ast_e:
                print(f"ast.literal_eval also failed: {ast_e}")
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
            SELECT ub.bookId, b.bookName, ub.pos, ub.mode 
            FROM user_books ub
            JOIN books b ON ub.bookId = b.id
            WHERE ub.userId = {user_id} 
            AND ub.isActive = true;
        """
        result = self._execute_safe_query(query, {'user_id': user_id})
        print(f"get_current_book. result: {result}")
        if not result or len(result[0].rows) == 0:
            return None, None, None, None
        data = self._text_to_json(str(result[0].rows[0]))
        # todo: перед возвратом сделать модель Book
        return data['ub.bookId'], data['b.bookName'], data['ub.pos'], data['ub.mode']

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
            SELECT ub.bookId as bookId, b.bookName as bookName
            FROM user_books ub
            JOIN books b ON ub.bookId = b.id
            WHERE ub.userId = {user_id};
        """

        result = self.db_adapter.execute_query(query)

        user_books = []

        for row in result[0].rows:
            data = self._text_to_json(str(row[0]))
            book_id = data['bookId']
            book_name = data['bookName']
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


    def update_book_mode(self, user_id, book_id, mode):
        # Update mode for specific user's book
        query = f"""
            UPDATE user_books 
            SET mode = "{mode}"
            WHERE userId = {user_id} AND bookId = {book_id};
        """
        self.db_adapter.execute_query(query)
        return 0


    def get_or_create_book(self, book_name):
        # Get book ID or create new book, return book_id
        if not book_name or book_name.strip() == "":
            print(f"❌ Ошибка: пустое имя книги")
            return None
        
        # Экранируем кавычки в имени книги для SQL запроса
        escaped_book_name = book_name.replace('"', '\\"')
        print(f"🔍 Ищем книгу: {book_name}")
        
        # First try to find existing book
        query = f"""
            SELECT id FROM books
            WHERE bookName = "{escaped_book_name}";
        """
        print(f"🔍 Выполняем запрос: {query}")
        result = self.db_adapter.execute_query(query)
        print(f"🔍 Результат поиска: {result}")
        
        if result and len(result[0].rows) > 0:
            # Book exists, return its ID
            print(f"✅ Книга найдена, извлекаем ID...")
            print(f"🔍 Сырой результат: {result[0].rows[0]}")
            print(f"🔍 Строковое представление: {str(result[0].rows[0])}")
            data = self._text_to_json(str(result[0].rows[0]))
            print(f"🔍 Распарсенные данные: {data}")
            book_id = data.get('id')
            if book_id is None:
                print(f"❌ Ошибка: не удалось извлечь ID книги из данных: {data}")
                return None
            print(f"✅ ID найденной книги: {book_id}")
            return book_id
        else:
            # Book doesn't exist, create new one
            print(f"📝 Книга не найдена, создаем новую...")
            
            # Get the next available ID by finding the maximum existing ID
            max_id_query = """
                SELECT MAX(id) as max_id FROM books;
            """
            print(f"🔍 Получаем максимальный ID: {max_id_query}")
            max_result = self.db_adapter.execute_query(max_id_query)
            print(f"🔍 Результат максимального ID: {max_result}")
            
            if max_result and len(max_result[0].rows) > 0:
                max_data = self._text_to_json(str(max_result[0].rows[0]))
                max_id = max_data.get('max_id')
                if max_id is None:
                    next_id = 1
                else:
                    next_id = int(max_id) + 1
            else:
                next_id = 1
            
            print(f"📝 Следующий ID: {next_id}")
            
            # Insert new book with the calculated ID
            query = f"""
                INSERT INTO books
                    (id, bookName, hash)
                VALUES
                    ({next_id}, "{escaped_book_name}", "");
            """
            print(f"📝 Выполняем INSERT: {query}")
            self.db_adapter.execute_query(query)
            print(f"✅ INSERT выполнен")
            
            print(f"✅ ID созданной книги: {next_id}")
            return next_id
