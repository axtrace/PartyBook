# Описание обработчика more
Все вызовы, связанные с командой `/more`. Сначала поищем в коде упоминания этой команды.

```mermaid
sequenceDiagram
    participant User
    participant TelebotHandler
    participant BookReader
    participant BooksLibrary
    participant DbManager
    participant YdbAdapter
    participant TxtFile

    User->>TelebotHandler: /more
    TelebotHandler->>BookReader: get_next_portion(user_id)
    BookReader->>BooksLibrary: get_current_book(user_id)
    BooksLibrary->>DbManager: get_current_book(user_id)
    DbManager->>YdbAdapter: execute_query(SELECT bookId, bookname, pos)
    YdbAdapter-->>DbManager: result
    DbManager-->>BooksLibrary: book_id, book_name, pos
    BooksLibrary-->>BookReader: book_id, file_name, pos
    BookReader->>TxtFile: read_piece(file_name, pos, piece_size)
    TxtFile-->>BookReader: text_piece, new_pos
    BookReader->>BooksLibrary: update_book_pos(user_id, file_name, new_pos)
    BooksLibrary->>DbManager: update_book_pos(user_id, book_id, new_pos)
    DbManager->>YdbAdapter: execute_query(UPDATE user_books_test)
    YdbAdapter-->>DbManager: result
    DbManager-->>BooksLibrary: success
    BooksLibrary-->>BookReader: success
    BookReader-->>TelebotHandler: text_piece
    TelebotHandler->>User: send_message(text_piece)
```

Текстовое описание процесса:

1. Пользователь отправляет команду `/more`
2. `TelebotHandler` получает сообщение и вызывает метод `get_next_portion(user_id)` класса `BookReader`
3. `BookReader` запрашивает текущую книгу пользователя через `BooksLibrary.get_current_book(user_id)`
4. `BooksLibrary` обращается к `DbManager` для получения информации о книге
5. `DbManager` выполняет SQL-запрос через `YdbAdapter` для получения ID книги, названия и текущей позиции
6. Полученная информация передается обратно через цепочку вызовов до `BookReader`
7. `BookReader` использует `TxtFile` для чтения следующей порции текста из файла книги
8. После чтения текста, `BookReader` обновляет позицию в книге через `BooksLibrary.update_book_pos()`
9. Обновление позиции проходит через `DbManager` и `YdbAdapter` для сохранения в базе данных
10. Прочитанный текст возвращается в `TelebotHandler`
11. `TelebotHandler` отправляет текст пользователю

Важные особенности:
- Система использует YDB (Yandex Database) для хранения данных
- Книги хранятся в текстовых файлах, а в базе данных хранятся только метаданные
- Позиция чтения (pos) обновляется после каждого чтения порции текста
- Система поддерживает многоязычность (ru/en)
- Есть поддержка автоматической отправки порций текста (isAutoSend)
