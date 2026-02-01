from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from pgvector.sqlalchemy import Vector
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    user_id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.now)
    
    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")
    settings = relationship("UserSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")

class UserSettings(Base):
    __tablename__ = "user_settings"
    
    user_id = Column(Integer, ForeignKey("users.user_id"), primary_key=True)
    enable_query_rewrite = Column(Boolean, default=False)
    rerank_top_k = Column(Integer, default=5)
    retrieval_top_k = Column(Integer, default=15)
    
    user = relationship("User", back_populates="settings")

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    filename = Column(String(255))
    content = Column(Text)
    uploaded_at = Column(DateTime, default=datetime.now)
    
    user = relationship("User", back_populates="documents")
    embeddings = relationship("Embedding", back_populates="document", cascade="all, delete-orphan")

class Embedding(Base):
    __tablename__ = "embeddings"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"))
    user_id = Column(Integer, ForeignKey("users.user_id"), index=True)
    chunk_text = Column(Text)
    embedding = Column(Vector(768))
    chunk_index = Column(Integer)
    document_name = Column(String(255))
    
    document = relationship("Document", back_populates="embeddings")

def init_db():
    """Создает все таблицы в БД"""

    Base.metadata.create_all(bind=engine)

def get_db():
    """Получает сессию БД"""

    db = SessionLocal()
    try:
        yield db

    finally:
        db.close()

def get_or_create_user(user_id):
    """Получает или создает пользователя"""
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(user_id=user_id).first()
        if not user:
            user = User(user_id=user_id)
            db.add(user)
            db.commit()
            
            settings = UserSettings(user_id=user_id)
            db.add(settings)
            db.commit()
        
        return user_id
    
    finally:
        db.close()

def get_user_settings(user_id):
    """Получает настройки пользователя"""

    db = SessionLocal()
    try:
        settings = db.query(UserSettings).filter_by(user_id=user_id).first()
        return {
            "enable_query_rewrite": settings.enable_query_rewrite,
            "rerank_top_k": settings.rerank_top_k,
            "retrieval_top_k": settings.retrieval_top_k
        } if settings else None
    
    finally:
        db.close()

def update_user_settings(user_id, **kwargs):
    """Обновляет настройки пользователя"""

    db = SessionLocal()
    try:
        settings = db.query(UserSettings).filter_by(user_id=user_id).first()
        if not settings:
            settings = UserSettings(user_id=user_id)
            db.add(settings)
        
        for key, value in kwargs.items():
            if hasattr(settings, key):
                setattr(settings, key, value)
        
        db.commit()
        return True
    
    finally:
        db.close()

def get_user_stats(user_id):
    """Получает статистику пользователя"""

    db = SessionLocal()
    try:
        num_documents = db.query(Document).filter_by(user_id=user_id).count()
        num_chunks = db.query(Embedding).filter_by(user_id=user_id).count()
        
        return {
            "user_id": user_id,
            "num_documents": num_documents,
            "num_chunks": num_chunks
        }
    
    finally:
        db.close()

def delete_user_data(user_id):
    """Удаляет все данные пользователя"""

    db = SessionLocal()
    try:
        db.query(Document).filter_by(user_id=user_id).delete()
        db.commit()
        return True
    
    finally:
        db.close()