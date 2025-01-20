from sqlalchemy import Column, Integer, String, DateTime, Text
from pgvector.sqlalchemy import Vector
from .database import Base
import datetime

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    role = Column(String)  # 'user' or 'assistant'
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

class BadenRAG(Base):
    __tablename__ = "baden_rag"

    id = Column(Integer, primary_key=True, index=True)
    fact = Column(Text)
    embedding = Column(Vector(512))
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)