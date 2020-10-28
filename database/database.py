import os
import sqlite3
from sqlalchemy import create_engine, Column, Integer, Boolean, String, VARCHAR, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

engine = create_engine('sqlite:///database/data.db', echo=True)
Base = declarative_base()
Session = sessionmaker(bind=engine)

# class Auth(Base):
#     __tablename__ = 'auth'
#     id = Column('pk', Integer, primary_key=True, nullable=False)
#     tg_id = Column('tg_id', Integer, unique=True, nullable=False)
#     auth = Column('auth', Boolean, default=0, nullable=False)
#     active = Column('active', Boolean, default=1, nullable=False)
#     banned = Column('banned', Boolean, default=0, nullable=False)


#     def __str__(self):
#         return f'User with {self.tg_id} telegram id'

class User(Base):
    __tablename__ = 'users'
    id = Column('pk', Integer, primary_key=True, nullable=False)
    tg_id = Column('tg_id', Integer, unique=True, nullable=False)
    username = Column('username', VARCHAR(50), unique=True)
    first_name = Column('first_name', VARCHAR(50), nullable=False)
    last_name = Column('last_name', VARCHAR(50))
    about = Column('about', VARCHAR(100))
    joined_date = Column('joined_date', DateTime, nullable=False)
    inviter_tg_id = Column('inviter_tg_id', Integer)
    inviter_username = Column('inviter_username', VARCHAR(50))
    inviter_first_name = Column('inviter_first_name', VARCHAR(50), nullable=False)
    invites = Column('invites', Integer, default=10)
    enter_chat_id = Column('enter_chat_id', Integer, nullable=False)

    def __str__(self):
        return f'User {self.username or self.first_name} with {self.tg_id} telegram id'

Base.metadata.create_all(bind=engine)

def create(model, **kwargs):
    print(model)
    print(kwargs)
    session = Session()
    # try:
    instance = model(**kwargs)
    session.add(instance)
    session.commit()
    # except:
    #     session.rollback()
    # finally:
    #     session.close()

def get(model, **kwargs):
    session = Session()
    try:
        instance = session.query(model).filter_by(**kwargs).first()
        if instance:
            return instance
        return None 
    finally:
        session.close()



# 1	111	username_RV87_test_bot	jopa			2020-10-28 13:56:17				0	
# 3	70635837	radioval87	Valentin	Gun		2020-10-28 13:56:17				-1001273799823	

# def get_or_create(session, model, **kwargs):
#     instance = session.query(model).filter_by(**kwargs).first()
#     if instance:
#         return instance
#     else:
#         instance = model(**kwargs)
#         session.add(instance)
#         session.commit()
#         return instance

# DB_PATH = './database/data.db'

# def init_db():
#     if os.path.isfile(DB_PATH) and os.path.getsize(DB_PATH) > 100:
#         with open(DB_PATH, 'r', encoding="ISO-8859-1") as f:
#             header = f.read(100)
#             if header.startswith('SQLite format 3'):
#                 print("SQLite3 database has been detected.")
#     else:
#         conn = sqlite3.connect(DB_PATH)

#         sql_create_auth_table = '''
#             CREATE TABLE IF NOT EXISTS auth
#                     (id             INTEGER(10)    NOT NULL     PRIMARY KEY,
#                     tg_id           INTEGER(10)    NOT NULL     UNIQUE,
#                     auth            BOOLEAN        NOT NULL     DEFAULT 0,
#                     active          BOOLEAN        NOT NULL     DEFAULT 1,
#                     banned          BOOLEAN        NOT NULL     DEFAULT 0);
#         '''
        
#         sql_create_users_table = '''
#             CREATE TABLE IF NOT EXISTS users
#                     (id             INTEGER(10)    NOT NULL     PRIMARY KEY,
#                     tg_id           INTEGER(10)    NOT NULL     UNIQUE,
#                     is_bot          BOOLEAN        NOT NULL,
#                     first_name      VARCHAR(50)    NOT NULL,
#                     last_name       VARCHAR(50),
#                     username        VARCHAR(50)                 UNIQUE,
#                     about           VARCHAR(100),
#                     joined_date     DATETIME       NOT NULL,
#                     inv_tg_id       INTEGER(10)                 UNIQUE,
#                     inv_username    VARCHAR(50)                 UNIQUE,
#                     invites         INTEGER(10)    NOT NULL     UNIQUE,
#                     enter_chat_id   INTEGER(19)    NOT NULL     UNIQUE,
#                     active          BOOLEAN        NOT NULL     DEFAULT 1,
#                     banned          BOOLEAN        NOT NULL     DEFAULT 0),
#                     FOREIGN KEY(tg_id) REFERENCES auth(tg_id) ON DELETE   CASCADE,
#                     FOREIGN KEY(author_nickname) REFERENCES users(nickname) ON DELETE   CASCADE);
#         '''
        

#         c = conn.cursor()
#         c.execute(sql_create_users_table)
#         conn.close()
#         print('Database has been created')

