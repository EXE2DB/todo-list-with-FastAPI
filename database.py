"""
This file's purpose is to define where the database is stored and how to interact with it.
Below I import some functions from necessary libraries.

To be honest, there is not much more to clarify here. The code explains itself pretty well, I think.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "sqlite:///./todo.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

#This will be later used by my classes in models.py to define my classes and their contents.
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()