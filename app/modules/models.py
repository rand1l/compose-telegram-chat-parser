from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, Text
from sqlalchemy import Column, BigInteger, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = Column(BigInteger, primary_key=True)
    username = Column(String(64), nullable=True)
    first_name = Column(String(128), nullable=True)
    last_name = Column(String(128), nullable=True)
    deleted = Column(Boolean, default=False)
    premium = Column(Boolean, default=False)

    history = relationship("UserHistory", back_populates="user")


class Chat(Base):
    __tablename__ = 'chats'

    id = Column(BigInteger, primary_key=True)
    title = Column(String(128), nullable=False)
    worker = Column(BigInteger, nullable=True)
    invite_link_id = Column(String(64), nullable=True)
    access_hash = Column(String(64), nullable=True)


class UserChat(Base):
    __tablename__ = 'user_chat'

    user_id = Column(BigInteger, ForeignKey('users.id'), primary_key=True)
    chat_id = Column(BigInteger, ForeignKey('chats.id'), primary_key=True)


class UserHistory(Base):
    __tablename__ = 'user_history'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    first_name = Column(String(128), nullable=True)
    last_name = Column(String(128), nullable=True)
    username = Column(String(64), nullable=True)
    deleted = Column(Boolean, nullable=True)
    premium = Column(Boolean, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="history")


class Message(Base):
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True, autoincrement=True)
    message_id = Column(BigInteger, nullable=False, unique=True)
    user_id = Column(BigInteger, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    chat_id = Column(BigInteger, ForeignKey('chats.id', ondelete='CASCADE'), nullable=False)
    message_text = Column(Text, nullable=False)
    timestamp = Column(DateTime, nullable=False)

    reply_to_message_id = Column(BigInteger, nullable=True)
    forwarded_from_user_id = Column(BigInteger, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)

    file_url = Column(Text, nullable=True)

    user = relationship("User", foreign_keys=[user_id])
    chat = relationship("Chat")
    forwarded_from_user = relationship("User", foreign_keys=[forwarded_from_user_id])
