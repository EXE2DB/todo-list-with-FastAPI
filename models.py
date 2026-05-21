"""
In this file I define the tables and their contents that I will use for my database.
I will comment important parts to clarify the intentions of the code.
"""

from sqlalchemy import Boolean, ForeignKey, Integer, String, Column
from sqlalchemy.orm import relationship
from database import Base

#Base is inherited so SQLAlchemy can interpret it as an SQL table and not just another python class.

class User(Base):
    #Here I define the tablename and its contents alongside their type.
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)

    #This is to establish a correlation between the Todolist class and User class.
    # Each Todolist will have a User as their owner.
    lists = relationship("TodoList", back_populates="owner", cascade="all, delete")

    #The classes below do the same thing as the one above.
    #Every object from Todo will have a Todolist object as their parent.
    # Same concept as every TodoList having a User as an "owner".

class TodoList(Base):
    __tablename__ = "todolists"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    owner = relationship("User", back_populates="lists")

    items = relationship("Todo", back_populates="list", cascade="all, delete")

class Todo(Base):
    __tablename__ = "todos"
    id = Column(Integer, primary_key=True, index=True)
    text = Column(String, nullable=False)
    done = Column(Boolean, default=False)
    list_id = Column(Integer, ForeignKey("todolists.id"), nullable=False)
    list = relationship("TodoList", back_populates="items")