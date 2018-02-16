import sqlite3


class DBHandler:
    def __init__(self):
        # Create table and DB if they does not exists
        conn = sqlite3.connect('books_pos_table.sqlite')
        cursor = conn.cursor()
        sql = """
            CREATE TABLE IF NOT EXISTS books_pos_table (
            userId INTEGER, 
            bookName TEXT UNIQUE,
            pos INTEGER);
            """
        cursor.executescript(sql)
        sql2 = """
            CREATE TABLE IF NOT EXISTS curent_book_table (
            userId INTEGER PRIMARY KEY, 
            chatId INTEGER,
            bookName TEXT UNIQUE,
            isAutoSend INTEGER);
            """
        cursor.executescript(sql2)
        cursor.close()
        conn.close()

    def update_book_pos(self, userId, bookName, newpos):
        # Update pos value for user and book
        conn = sqlite3.connect('books_pos_table.sqlite')
        cursor = conn.cursor()
        sql = """
        INSERT OR IGNORE INTO books_pos_table (userId, bookName, pos) VALUES({0}, \"{1}\", {2});
        UPDATE books_pos_table SET pos={2} WHERE userId={0} and bookName=\"{1}\";
        """.format(userId, bookName, newpos)
        cursor.executescript(sql)
        cursor.close()
        conn.close()
        return 0

    def update_current_book(self, userId, chatId, bookName):
        # Update book currently reading by user
        conn = sqlite3.connect('books_pos_table.sqlite')
        cursor = conn.cursor()
        sql = """
        INSERT OR IGNORE INTO curent_book_table (userId, chatId, bookName, isAutoSend) VALUES({0}, {1}, \"{2}\", {3});
        UPDATE curent_book_table SET bookName=\"{2}\", isAutoSend=1 WHERE userId={0};
        """.format(userId, chatId, bookName, 1)
        cursor.executescript(sql)
        cursor.close()
        conn.close()
        return 0

    def get_current_book(self, userId):
        # get current book of user
        conn = sqlite3.connect('books_pos_table.sqlite')
        cursor = conn.cursor()
        sql = """
        SELECT bookname FROM curent_book_table WHERE userId={0};
        """.format(userId)
        cursor.execute(sql)
        fetchone = cursor.fetchone()
        cursor.close()
        conn.close()

        if fetchone is None:
            res = -1
        else:
            res = str(fetchone[0])
        return res

    def update_auto_status(self, userId):
        # change status of auto-sending
        conn = sqlite3.connect('books_pos_table.sqlite')
        cursor = conn.cursor()
        sql = """
         UPDATE curent_book_table SET isAutoSend=1-isAutoSend WHERE userId={0};
         """.format(userId)
        cursor.executescript(sql)
        cursor.close()
        conn.close()
        return 0

    def get_auto_status(self, userId):
        # return status of auto-sending
        conn = sqlite3.connect('books_pos_table.sqlite')
        cursor = conn.cursor()
        sql = """
            SELECT isAutoSend FROM curent_book_table WHERE userId={0};
            """.format(userId)
        cursor.execute(sql)
        fetchone = cursor.fetchone()
        cursor.close()
        conn.close()

        if fetchone is None:
            res = -1
        else:
            res = int(fetchone[0])
        return res

    def get_user_books(self, userId):
        # Return all user's books
        conn = sqlite3.connect('books_pos_table.sqlite')
        cursor = conn.cursor()
        sql = """
        SELECT bookName FROM books_pos_table WHERE userId={0};
        """.format(userId)
        cursor.execute(sql)
        select_res = cursor.fetchall()
        cursor.close()
        conn.close()
        res = list()
        for item in select_res:
            res.append(item[0])
        return res

    def get_users_for_autosend(self):
        # Return all user with auto-sending ON
        conn = sqlite3.connect('books_pos_table.sqlite')
        cursor = conn.cursor()
        sql = """
        SELECT userId, chatId FROM curent_book_table WHERE isAutoSend=1;
        """
        cursor.execute(sql)
        select_res = cursor.fetchall()
        cursor.close()
        conn.close()
        return select_res

    def get_pos(self, userId, bookName):
        # Return pos value for user and book
        conn = sqlite3.connect('books_pos_table.sqlite')
        cursor = conn.cursor()
        sql = """
        SELECT pos FROM books_pos_table WHERE userId={0} and bookName=\"{1}\";
        """.format(userId, bookName)
        cursor.execute(sql)
        fetchone = cursor.fetchone()
        if fetchone is None:
            res = -1
        else:
            res = int(fetchone[0])
        cursor.close()
        conn.close()
        return res
