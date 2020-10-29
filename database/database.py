import os
import sqlite3

from sqlalchemy import (VARCHAR, Boolean, Column, DateTime, Integer, String,
                        create_engine)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

engine = create_engine('sqlite:///database/data.db', echo=False)
Base = declarative_base()
Session = sessionmaker(bind=engine)


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
    try:
        instance = model(**kwargs)
        session.add(instance)
        session.commit()
    except:
        session.rollback()
    finally:
        session.close()

def get(model, **kwargs):
    session = Session()
    try:
        instance = session.query(model).filter_by(**kwargs).first()
        if instance:
            return instance
        return None 
    finally:
        session.close()

# def get_or_create(session, model, **kwargs):
#     instance = session.query(model).filter_by(**kwargs).first()
#     if instance:
#         return instance
#     else:
#         instance = model(**kwargs)
#         session.add(instance)
#         session.commit()
#         return instance
