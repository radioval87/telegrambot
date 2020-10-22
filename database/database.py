import os
import sqlite3

DB_PATH = './database/data.db'

def init_db():
    if os.path.isfile(DB_PATH) and os.path.getsize(DB_PATH) > 100:
        with open(DB_PATH, 'r', encoding="ISO-8859-1") as f:
            header = f.read(100)
            if header.startswith('SQLite format 3'):
                print("SQLite3 database has been detected.")
    else:
        conn = sqlite3.connect(DB_PATH)

        sql_create_users_table = '''
            CREATE TABLE IF NOT EXISTS users
                    (id             INTEGER(10)    NOT NULL     PRIMARY KEY,
                    tg_id           INTEGER(10)    NOT NULL     UNIQUE,
                    is_bot          BOOLEAN        NOT NULL,
                    first_name      VARCHAR(50)    NOT NULL,
                    last_name       VARCHAR(50),
                    username        VARCHAR(50)                 UNIQUE,
                    about           VARCHAR(100),
                    joined_date     DATETIME       NOT NULL,
                    inv_tg_id       INTEGER(10)                 UNIQUE,
                    inv_username    VARCHAR(50)                 UNIQUE,
                    invites         INTEGER(10)    NOT NULL     UNIQUE,
                    enter_chat_id   INTEGER(19)    NOT NULL     UNIQUE,
                    auth            BOOLEAN        NOT NULL     DEFAULT 0,
                    active          BOOLEAN        NOT NULL     DEFAULT 1,
                    banned          BOOLEAN        NOT NULL     DEFAULT 0);
        '''

        c = conn.cursor()
        c.execute(sql_create_users_table)
        conn.close()
        print('Database has been created')
