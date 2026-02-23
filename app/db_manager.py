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

    def _execute_parameterized_query(self, query, parameters=None):
        """
        Выполняет параметризованный запрос к YDB

        Args:
            query: SQL запрос с параметрами вида $param_name
            parameters: Словарь параметров {'$param_name': value}

        Returns:
            Результат выполнения запроса или None в случае ошибки
        """
        try:
            result = self.db_adapter.execute_query(query, parameters)
            return result
        except Exception as e:
            print(f"Error executing parameterized query: {str(e)}")
            print(f"Query: {query}")
            print(f"Parameters: {parameters}")
            return None

    def update_book_pos(self, user_id, book_id, newpos):
        query = """
            DECLARE $user_id AS Uint64;
            DECLARE $book_id AS Uint64;
            DECLARE $newpos AS Uint64;

            UPDATE user_books
            SET pos = $newpos
            WHERE userId = $user_id AND bookId = $book_id;
        """
        return self._execute_parameterized_query(query, {
            '$user_id': user_id,
            '$book_id': book_id,
            '$newpos': newpos
        })

    def update_current_book(self, user_id, book_id):
        # Деактивируем предыдущую активную книгу пользователя
        deactivate_query = """
            DECLARE $user_id AS Uint64;

            UPDATE user_books
            SET isActive = false
            WHERE userId = $user_id AND isActive = true;
        """
        self._execute_parameterized_query(deactivate_query, {'$user_id': user_id})

        # Активируем новую книгу
        # Сначала проверяем, существует ли запись
        check_query = """
            DECLARE $user_id AS Uint64;
            DECLARE $book_id AS Uint64;

            SELECT id FROM user_books
            WHERE userId = $user_id AND bookId = $book_id;
        """
        result = self._execute_parameterized_query(check_query, {
            '$user_id': user_id,
            '$book_id': book_id
        })

        if result and len(result[0].rows) > 0:
            # Запись существует, обновляем её
            update_query = """
                DECLARE $user_id AS Uint64;
                DECLARE $book_id AS Uint64;

                UPDATE user_books
                SET isActive = true
                WHERE userId = $user_id AND bookId = $book_id;
            """
            self._execute_parameterized_query(update_query, {
                '$user_id': user_id,
                '$book_id': book_id
            })
        else:
            # Записи нет, создаем новую с уникальным id
            # Получаем максимальный ID из таблицы user_books
            max_id_query = "SELECT MAX(id) as max_id FROM user_books;"
            max_result = self.db_adapter.execute_query(max_id_query)

            next_id = 1  # По умолчанию
            if max_result and len(max_result[0].rows) > 0:
                try:
                    max_data = self._text_to_json(str(max_result[0].rows[0]))
                    max_id = max_data.get('max_id')
                    if max_id is not None:
                        next_id = int(max_id) + 1
                except Exception as e:
                    print(f"⚠️ Ошибка получения max_id для user_books: {e}")
                    try:
                        raw_max_id = max_result[0].rows[0][0]
                        if raw_max_id is not None:
                            next_id = int(raw_max_id) + 1
                    except Exception as e2:
                        print(f"⚠️ Ошибка получения max_id (способ 2): {e2}")

            insert_query = """
                DECLARE $id AS Uint64;
                DECLARE $user_id AS Uint64;
                DECLARE $book_id AS Uint64;

                INSERT INTO user_books (id, userId, bookId, isActive)
                VALUES ($id, $user_id, $book_id, true);
            """
            self._execute_parameterized_query(insert_query, {
                '$id': next_id,
                '$user_id': user_id,
                '$book_id': book_id
            })

        return 0

    def update_auto_status(self, user_id, status_to):
        # change status of auto-sending
        new_status = self.bool_to_str(status_to)

        # Сначала проверяем, существует ли пользователь
        check_query = """
            DECLARE $user_id AS Uint64;

            SELECT userId FROM users WHERE userId = $user_id;
        """
        result = self._execute_parameterized_query(check_query, {'$user_id': user_id})

        if result and len(result[0].rows) > 0:
            # Пользователь существует, обновляем
            query = """
                DECLARE $user_id AS Uint64;
                DECLARE $is_auto_send AS Bool;

                UPDATE users
                SET isAutoSend = $is_auto_send
                WHERE userId = $user_id;
            """
            self._execute_parameterized_query(query, {
                '$user_id': user_id,
                '$is_auto_send': status_to
            })
        else:
            # Пользователя нет, создаем с уникальным числовым id
            # Получаем максимальный ID из таблицы users
            max_id_query = "SELECT MAX(id) as max_id FROM users;"
            max_result = self.db_adapter.execute_query(max_id_query)

            next_id = 1  # По умолчанию
            if max_result and len(max_result[0].rows) > 0:
                try:
                    max_data = self._text_to_json(str(max_result[0].rows[0]))
                    max_id = max_data.get('max_id')
                    if max_id is not None:
                        next_id = int(max_id) + 1
                except Exception as e:
                    print(f"⚠️ Ошибка получения max_id для users: {e}")
                    try:
                        raw_max_id = max_result[0].rows[0][0]
                        if raw_max_id is not None:
                            next_id = int(raw_max_id) + 1
                    except Exception as e2:
                        print(f"⚠️ Ошибка получения max_id (способ 2): {e2}")

            query = """
                DECLARE $id AS Uint64;
                DECLARE $user_id AS Uint64;
                DECLARE $is_auto_send AS Bool;

                INSERT INTO users (id, userId, isAutoSend)
                VALUES ($id, $user_id, $is_auto_send);
            """
            self._execute_parameterized_query(query, {
                '$id': next_id,
                '$user_id': user_id,
                '$is_auto_send': status_to
            })

        return 0

    def update_user_lang(self, user_id, lang):
        # change lang for user

        # Сначала проверяем, существует ли пользователь
        check_query = """
            DECLARE $user_id AS Uint64;

            SELECT userId FROM users WHERE userId = $user_id;
        """
        result = self._execute_parameterized_query(check_query, {'$user_id': user_id})

        if result and len(result[0].rows) > 0:
            # Пользователь существует, обновляем
            query = """
                DECLARE $user_id AS Uint64;
                DECLARE $lang AS Utf8;

                UPDATE users
                SET lang = $lang
                WHERE userId = $user_id;
            """
            self._execute_parameterized_query(query, {
                '$user_id': user_id,
                '$lang': lang
            })
        else:
            # Пользователя нет, создаем с уникальным числовым id
            # Получаем максимальный ID из таблицы users
            max_id_query = "SELECT MAX(id) as max_id FROM users;"
            max_result = self.db_adapter.execute_query(max_id_query)

            next_id = 1  # По умолчанию
            if max_result and len(max_result[0].rows) > 0:
                try:
                    max_data = self._text_to_json(str(max_result[0].rows[0]))
                    max_id = max_data.get('max_id')
                    if max_id is not None:
                        next_id = int(max_id) + 1
                except Exception as e:
                    print(f"⚠️ Ошибка получения max_id для users: {e}")
                    try:
                        raw_max_id = max_result[0].rows[0][0]
                        if raw_max_id is not None:
                            next_id = int(raw_max_id) + 1
                    except Exception as e2:
                        print(f"⚠️ Ошибка получения max_id (способ 2): {e2}")

            query = """
                DECLARE $id AS Uint64;
                DECLARE $user_id AS Uint64;
                DECLARE $lang AS Utf8;

                INSERT INTO users (id, userId, lang)
                VALUES ($id, $user_id, $lang);
            """
            self._execute_parameterized_query(query, {
                '$id': next_id,
                '$user_id': user_id,
                '$lang': lang
            })

        return 0

    def get_current_book(self, user_id):
        query = """
            DECLARE $user_id AS Uint64;

            SELECT ub.bookId, b.bookName, ub.pos, ub.mode
            FROM user_books ub
            JOIN books b ON ub.bookId = b.id
            WHERE ub.userId = $user_id
            AND ub.isActive = true;
        """
        result = self._execute_parameterized_query(query, {'$user_id': user_id})
        print(f"get_current_book. result: {result}")
        if not result or len(result[0].rows) == 0:
            return None, None, None, None
        data = self._text_to_json(str(result[0].rows[0]))
        # todo: перед возвратом сделать модель Book
        return data['ub.bookId'], data['b.bookName'], data['ub.pos'], data['ub.mode']

    def get_auto_status(self, user_id):
        # return status of auto-sending
        query = """
            DECLARE $user_id AS Uint64;

            SELECT isAutoSend FROM users
            WHERE userId = $user_id;
        """
        result = self._execute_parameterized_query(query, {'$user_id': user_id})
        if len(result[0].rows) == 1:
            data = self._text_to_json(str(result[0].rows[0]))
            status = self.str_to_bool(data['isAutoSend'])
            return status
        return -1

    def get_user_books(self, user_id):
        # Return all user's books
        query = """
            DECLARE $user_id AS Uint64;

            SELECT ub.bookId as bookId, b.bookName as bookName
            FROM user_books ub
            JOIN books b ON ub.bookId = b.id
            WHERE ub.userId = $user_id;
        """

        result = self._execute_parameterized_query(query, {'$user_id': user_id})

        user_books = []

        for row in result[0].rows:
            data = self._text_to_json(str(row[0]))
            book_id = data['bookId']
            book_name = data['bookName']
            user_books.append({book_id: book_name})

        return user_books

    def get_users_for_autosend(self):
        # Return all user with auto-sending ON

        query = """
            SELECT userId FROM users
            WHERE isAutoSend = true;
        """
        result = self._execute_parameterized_query(query)

        user_ids = []

        for row in result[0].rows:
            data = self._text_to_json(row)
            user_id = data['userId']
            user_ids.append(user_id)

        return user_ids

    def get_book_pos(self, user_id, book_id):
        # Return pos value for user and book
        query = """
            DECLARE $user_id AS Uint64;
            DECLARE $book_id AS Uint64;

            SELECT bookId, pos FROM user_books
            WHERE userId = $user_id AND bookId = $book_id;
        """
        result = self._execute_parameterized_query(query, {
            '$user_id': user_id,
            '$book_id': book_id
        })
        if len(result[0].rows) == 1:
            data = self._text_to_json(str(result[0].rows[0]))
            book_id = data['bookId']
            book_pos = data['pos']
            return book_id, book_pos
        return -1


    def get_user_lang(self, user_id):
        # Return lang for user
        query = """
            DECLARE $user_id AS Uint64;

            SELECT lang FROM users
            WHERE userId = $user_id;
        """

        result = self._execute_parameterized_query(query, {'$user_id': user_id})

        if len(result[0].rows) == 1:
            data = self._text_to_json(str(result[0].rows[0]))
            lang = data['lang']
            return lang
        return None

    def save_chunk(self, book_id, chunk_id, text):
        # Используем параметризованный запрос
        query = """
            DECLARE $book_id AS Uint64;
            DECLARE $chunk_id AS Uint64;
            DECLARE $text AS Utf8;

            INSERT INTO book_chunks (bookId, chunkId, text)
            VALUES ($book_id, $chunk_id, $text);
        """

        try:
            self._execute_parameterized_query(query, {
                '$book_id': book_id,
                '$chunk_id': chunk_id,
                '$text': text
            })
            return 0
        except Exception as e:
            print(f"❌ Ошибка сохранения чанка {chunk_id} для книги {book_id}: {e}")
            raise e

    def save_chunks_batch(self, book_id, chunks_list):
        """
        БАТЧИНГ: Сохраняем множество чанков
        Использует параметризованные запросы для безопасности
        """
        if not chunks_list:
            return 0

        # Получаем текущее количество чанков ОДИН РАЗ
        current_chunk_count = self.get_total_chunks(book_id)

        # YDB не поддерживает массовые параметризованные вставки напрямую
        # Поэтому используем отдельные параметризованные INSERT'ы
        # Это безопаснее, чем старый батчинг с конкатенацией строк

        chunks_created = 0
        print(f"🚀 БАТЧИНГ: Сохраняем {len(chunks_list)} чанков параметризованными запросами")

        for i, chunk_text in enumerate(chunks_list):
            try:
                chunk_id = current_chunk_count + i
                self.save_chunk(book_id, chunk_id, chunk_text)
                chunks_created += 1
            except Exception as e:
                print(f"❌ Ошибка сохранения чанка {chunk_id}: {e}")
                break

        print(f"✅ БАТЧИНГ: Успешно сохранено {chunks_created} чанков")
        return chunks_created

    def _save_chunks_individually(self, book_id, chunks_list, start_chunk_id):
        """Fallback: сохраняем чанки по одному"""
        chunks_created = 0
        for i, chunk_text in enumerate(chunks_list):
            try:
                chunk_id = start_chunk_id + i
                self.save_chunk(book_id, chunk_id, chunk_text)
                chunks_created += 1
            except Exception as e:
                print(f"❌ Ошибка сохранения чанка {chunk_id}: {e}")
                break
        return chunks_created

    def get_chunk(self, book_id, chunk_id):
        query = """
            DECLARE $book_id AS Uint64;
            DECLARE $chunk_id AS Uint64;

            SELECT text FROM book_chunks
            WHERE bookId = $book_id AND chunkId = $chunk_id;
        """
        result = self._execute_parameterized_query(query, {
            '$book_id': book_id,
            '$chunk_id': chunk_id
        })
        if not result or len(result[0].rows) == 0:
            return None
        data = self._text_to_json(str(result[0].rows[0]))
        return data['text']

    def get_total_chunks(self, book_id):
        query = """
            DECLARE $book_id AS Uint64;

            SELECT COUNT(*) as count FROM book_chunks
            WHERE bookId = $book_id;
        """
        result = self._execute_parameterized_query(query, {'$book_id': book_id})
        if len(result[0].rows) == 0:
            return 0
        data = self._text_to_json(str(result[0].rows[0]))
        return data['count']


    def update_book_mode(self, user_id, book_id, mode):
        # Update mode for specific user's book
        query = """
            DECLARE $user_id AS Uint64;
            DECLARE $book_id AS Uint64;
            DECLARE $mode AS Utf8;

            UPDATE user_books
            SET mode = $mode
            WHERE userId = $user_id AND bookId = $book_id;
        """
        self._execute_parameterized_query(query, {
            '$user_id': user_id,
            '$book_id': book_id,
            '$mode': mode
        })
        return 0


    def get_or_create_book(self, book_name):
        # Get book ID or create new book, return book_id
        if not book_name or book_name.strip() == "":
            print(f"❌ Ошибка: пустое имя книги")
            return None

        print(f"🔍 Ищем книгу: {book_name}")

        # First try to find existing book using parameterized query
        query = """
            DECLARE $book_name AS Utf8;
            SELECT id FROM books
            WHERE bookName = $book_name;
        """
        print(f"🔍 Выполняем параметризованный запрос поиска книги")
        result = self._execute_parameterized_query(query, {'$book_name': book_name})
        print(f"🔍 Результат поиска: {result}")

        if result and len(result[0].rows) > 0:
            # Book exists, return its ID
            print(f"✅ Книга найдена, извлекаем ID...")
            print(f"🔍 Сырой результат: {result[0].rows[0]}")
            print(f"🔍 Строковое представление: {str(result[0].rows[0])}")

            # Пробуем разные способы извлечения ID
            try:
                # Способ 1: через _text_to_json
                data = self._text_to_json(str(result[0].rows[0]))
                print(f"🔍 Распарсенные данные: {data}")
                book_id = data.get('id')
                if book_id is not None:
                    print(f"✅ ID найденной книги (способ 1): {book_id}")
                    return int(book_id)
                else:
                    print(f"⚠️ ID книги в БД равен NULL - это ошибка данных!")
            except Exception as e:
                print(f"⚠️ Способ 1 не сработал: {e}")

            try:
                # Способ 2: прямое извлечение из результата
                raw_id = result[0].rows[0][0]  # Первый столбец первой строки
                print(f"🔍 Прямой ID: {raw_id}")
                if raw_id is not None:
                    book_id = int(raw_id)
                    print(f"✅ ID найденной книги (способ 2): {book_id}")
                    return book_id
                else:
                    print(f"⚠️ ID книги в БД равен NULL - это ошибка данных!")
            except Exception as e:
                print(f"⚠️ Способ 2 не сработал: {e}")

            # Если книга найдена, но ID = NULL, это критическая ошибка данных
            # Удаляем битую запись и создаем новую
            print(f"🔧 Удаляем битую запись с NULL id...")
            delete_query = """
                DECLARE $book_name AS Utf8;

                DELETE FROM books
                WHERE bookName = $book_name AND id IS NULL;
            """
            self._execute_parameterized_query(delete_query, {'$book_name': book_name})
            print(f"✅ Битая запись удалена, создаем новую...")
            # Продолжаем создание новой записи ниже
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

            next_id = 1  # По умолчанию

            if max_result and len(max_result[0].rows) > 0:
                try:
                    # Способ 1: через _text_to_json
                    max_data = self._text_to_json(str(max_result[0].rows[0]))
                    max_id = max_data.get('max_id')
                    if max_id is not None:
                        next_id = int(max_id) + 1
                except Exception as e:
                    print(f"⚠️ Способ 1 для max_id не сработал: {e}")
                    try:
                        # Способ 2: прямое извлечение
                        raw_max_id = max_result[0].rows[0][0]
                        if raw_max_id is not None:
                            next_id = int(raw_max_id) + 1
                    except Exception as e2:
                        print(f"⚠️ Способ 2 для max_id не сработал: {e2}")

            print(f"📝 Следующий ID: {next_id}")

            # Insert new book with the calculated ID using parameterized query
            insert_query = """
                DECLARE $book_id AS Uint64;
                DECLARE $book_name AS Utf8;
                DECLARE $hash AS Utf8;

                INSERT INTO books (id, bookName, hash)
                VALUES ($book_id, $book_name, $hash);
            """
            print(f"📝 Выполняем параметризованный INSERT")
            self._execute_parameterized_query(insert_query, {
                '$book_id': next_id,
                '$book_name': book_name,
                '$hash': ""
            })
            print(f"✅ INSERT выполнен")

            print(f"✅ ID созданной книги: {next_id}")
            return next_id

    def update_user_time(self, user_id, time_str):
        """Обновляет время автопересылки для пользователя"""
        check_query = """
            DECLARE $user_id AS Uint64;

            SELECT userId FROM users WHERE userId = $user_id;
        """
        result = self._execute_parameterized_query(check_query, {'$user_id': user_id})

        if result and len(result[0].rows) > 0:
            query = """
                DECLARE $user_id AS Uint64;
                DECLARE $time AS Utf8;

                UPDATE users
                SET time = $time
                WHERE userId = $user_id;
            """
            self._execute_parameterized_query(query, {
                '$user_id': user_id,
                '$time': time_str
            })
        else:
            # Пользователя нет, создаем с уникальным числовым id
            max_id_query = "SELECT MAX(id) as max_id FROM users;"
            max_result = self.db_adapter.execute_query(max_id_query)

            next_id = 1  # По умолчанию
            if max_result and len(max_result[0].rows) > 0:
                try:
                    max_data = self._text_to_json(str(max_result[0].rows[0]))
                    max_id = max_data.get('max_id')
                    if max_id is not None:
                        next_id = int(max_id) + 1
                except Exception as e:
                    print(f"⚠️ Ошибка получения max_id для users: {e}")
                    try:
                        raw_max_id = max_result[0].rows[0][0]
                        if raw_max_id is not None:
                            next_id = int(raw_max_id) + 1
                    except Exception as e2:
                        print(f"⚠️ Ошибка получения max_id (способ 2): {e2}")

            query = """
                DECLARE $id AS Uint64;
                DECLARE $user_id AS Uint64;
                DECLARE $time AS Utf8;

                INSERT INTO users (id, userId, time)
                VALUES ($id, $user_id, $time);
            """
            self._execute_parameterized_query(query, {
                '$id': next_id,
                '$user_id': user_id,
                '$time': time_str
            })

        return 0

    def get_users_for_auto_send_by_time(self, current_time):
        """
        Получает пользователей для автопересылки по их предпочтительному времени

        Args:
            current_time: Текущее время (datetime)

        Returns:
            list: Список пользователей с их данными
        """
        # Получаем текущее время в формате HH:MM
        current_time_str = current_time.strftime("%H:%M")

        # Получаем всех пользователей с включенной автопересылкой
        query = """
            DECLARE $current_time AS Utf8;

            SELECT userId, chatId, lang, time FROM users
            WHERE isAutoSend = true
            AND time != ""
            AND time = $current_time;
        """

        result = self._execute_parameterized_query(query, {'$current_time': current_time_str})
        users = []

        if result and len(result[0].rows) > 0:
            for row in result[0].rows:
                try:
                    data = self._text_to_json(str(row))
                    users.append({
                        'user_id': data['userId'],
                        'chat_id': data['chatId'],
                        'lang': data.get('lang', 'ru'),
                        'time': data['time']
                    })
                except Exception as e:
                    print(f"❌ Ошибка парсинга данных пользователя: {e}")
                    continue

        print(f"📊 Найдено {len(users)} пользователей для автопересылки в {current_time_str}")
        return users
