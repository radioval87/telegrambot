import logging

from sqlalchemy import (VARCHAR, Boolean, Column, DateTime, ForeignKey,
                        Integer, create_engine, event)
from sqlalchemy.engine import Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from tools.miscellaneous import add_logger_err

engine = create_engine('sqlite:///database/data.db', echo=False)
Base = declarative_base()
Session = sessionmaker(bind=engine)

logger = logging.getLogger('main_bot').setLevel(logging.WARNING)
logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

class Chat(Base):
    __tablename__ = 'chats'
    id = Column('id', Integer, primary_key=True, nullable=False)
    chat_id = Column('chat_id', Integer, unique=True, nullable=False)
    chat_title = Column('chat_title', VARCHAR(50))
    ban_mode = Column('ban_mode', Boolean, default=0)

    def __str__(self):
        return (f'Chat {self.chat_title} with {self.chat_id}.' +
                f' Ban mode:{self.ban_mode}')


class User(Base):
    __tablename__ = 'users'
    id = Column('id', Integer, primary_key=True, nullable=False)
    tg_id = Column('tg_id', Integer, nullable=False)
    username = Column('username', VARCHAR(50), nullable=True)
    first_name = Column('first_name', VARCHAR(50), nullable=False)
    last_name = Column('last_name', VARCHAR(50))
    about = Column('about', VARCHAR(100))
    joined_date = Column('joined_date', DateTime, nullable=False)
    inviter_tg_id = Column('inviter_tg_id', Integer)
    inviter_username = Column('inviter_username', VARCHAR(50))
    inviter_first_name = Column('inviter_first_name', VARCHAR(50),
                                nullable=False)
    invites = Column('invites', Integer, default=10)
    enter_chat_id = Column('enter_chat_id', Integer, ForeignKey('chats.chat_id'),
                           nullable=True)

    def __str__(self):
        if self.username != 'NULL':
            return f'User {self.username} with {self.tg_id} telegram id'
        return f'User {self.first_name} with {self.tg_id} telegram id'

class Message(Base):
    __tablename__ = 'messages'
    id = Column('id', Integer, primary_key=True, nullable=False)
    from_id = Column('from_id', Integer, ForeignKey('users.id'),
                     nullable=False)
    from_username = Column('username', VARCHAR(50), nullable=True)
    from_first_name = Column('first_name', VARCHAR(50), nullable=False)
    msg_date = Column('msg_date', DateTime, nullable=False)
    msg_type = Column('msg_type', VARCHAR(20))
    text = Column('text', VARCHAR(4096), nullable=True)
    chat_id = Column('chat_id', Integer, ForeignKey('chats.chat_id'),
                     nullable=False)
    mat = Column('mat', Boolean, nullable=False)
    caps = Column('caps', Boolean, nullable=False)

    def __str__(self):
        return (f'Message from {self.from_username or self.from_first_name}' +
                f' in {self.chat_id} chat')


Base.metadata.create_all(bind=engine)

def create(model, **kwargs):
    session = Session()
    try:
        instance = model(**kwargs)
        session.add(instance)
        session.commit()
        logging.info('Message added to DB')
    except Exception as e:
        add_logger_err(e)
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
    except Exception as e:
        add_logger_err(e)
    finally:
        session.close()

def get_or_create(model, **kwargs):
    session = Session()
    try:
        instance = session.query(model).filter_by(**kwargs).first()
        if instance:
            return instance
        else:
            instance = model(**kwargs)
            session.add(instance)
            session.commit()
            return instance
    except Exception as e:
        add_logger_err(e)
        session.rollback()
    finally:
        session.close()

def update_invites(user_id, value):
    session = Session()
    try:
        user = session.query(User).filter_by(tg_id=user_id).first()
        user.invites = user.invites + value
        session.commit()
    except Exception as e:
        add_logger_err(e)
    finally:
        session.close()
