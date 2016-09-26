# -*- coding: utf-8 -*-

from crispy_forms.layout import Column
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Boolean, DECIMAL, String, TEXT, DATETIME, ForeignKey
from sqlalchemy import create_engine
from urllib import quote_plus as urlquote
from sqlalchemy.orm import relationship, sessionmaker
import logging
import datetime
Base = declarative_base()


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False)
    chat_id = Column(String(50), nullable=True)
    first_name = Column(String(50))
    last_name = Column(String(100))
    active_dong = Column(Integer, nullable=True)

    def __repr__(self):
        return "<User(name='%s', fullname='%s', code='%s')>" % (
            self.name, self.fullname, self.code)


class Dong(Base):
    __tablename__ = 'dong'
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(50))
    join_key = Column(String(10))
    joinable = Column(Boolean, default=True)

    def __repr__(self):
        return "<Dong(title={}, join_key={}, joinable={})>"\
            .format(self.title, self.join_key, self.joinable)


class UserDong(Base):
    __tablename__ = 'user_dong'
    id = Column(Integer, primary_key=True, autoincrement=True)
    is_admin = Column(Boolean, default=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship("User", back_populates="user_dong")

    dong_id = Column(Integer, ForeignKey('dong.id'))
    dong = relationship("Dong", back_populates="user_dong")

    balance = Column(DECIMAL(10), default=0)

    def __repr__(self):
        return "<UserDong(balance={})>".format(self.balance)

User.user_dong = relationship(
     "UserDong", order_by=UserDong.id, back_populates="user")
Dong.user_dong = relationship(
     "UserDong", order_by=UserDong.id, back_populates="dong")


class Expense(Base):
    __tablename__ = 'expense'
    id = Column(Integer, primary_key=True, autoincrement=True)
    payment = Column(DECIMAL(10))
    description = Column(TEXT)
    debit_type = Column(Integer)
    created_date = Column(DATETIME, default=datetime.datetime.utcnow)

    user_dong_id = Column(Integer, ForeignKey('user_dong.id'))
    user_dong = relationship("UserDong", back_populates="expense")

UserDong.expense = relationship(
     "Expense", order_by=Expense.id, back_populates="user_dong")


class Article(Base):
    __tablename__ = 'article'
    id = Column(Integer, primary_key=True, autoincrement=True)
    credit = Column(DECIMAL(10), default=0)
    debit = Column(DECIMAL(10), default=0)
    created_date = Column(DATETIME, default=datetime.datetime.utcnow)

    expense_id = Column(Integer, ForeignKey('expense.id'))
    expense = relationship("Expense", back_populates="article")

    user_dong_id = Column(Integer, ForeignKey('user_dong.id'))
    user_dong = relationship("UserDong", back_populates="article")

Expense.article = relationship(
     "Article", order_by=Article.id, back_populates="expense")
UserDong.article = relationship(
     "Article", order_by=Article.id, back_populates="user_dong")


db_username = 'root'
db_password = '123!@#'
engine = create_engine("mysql://{}:{}@localhost/test?charset=utf8".format(urlquote(db_username),
                                                                          urlquote(db_password)),
                       isolation_level="READ UNCOMMITTED",
                       echo=True)

Session = sessionmaker()


def create_models():
    logging.info('Creating all models')
    Base.metadata.create_all(engine)
    Session.configure(bind=engine)
