from datetime import datetime
from typing import List
from sqlalchemy import JSON, ForeignKey, func
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Column, Integer, String, ForeignKey, Date, Boolean
from sqlalchemy.ext.declarative import declarative_base


# class Base(AsyncAttrs, DeclarativeBase):
#     pass

Base = declarative_base()


class Users(Base):
    __tablename__ = "users"

    id = Column(String(100), primary_key=True)
    username = Column(String(100))
    first_name = Column(String(100))
    last_name = Column(String(100))


class Cases(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True)
    user_id = Column(String(100), ForeignKey("users.id"))
    name = Column(String(100))
    start_date = Column(Date, nullable=False)
    description = Column(String(100))
    deadline_date = Column(Date, nullable=True)
    repeat = Column(String(100))
    is_finished = Column(Boolean, default=False)


class File(Base):
    __tablename__ = 'file'
    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.id"))
    file_name = Column(String(100))
    file_url = Column(String(100))
