import os
import uuid
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, Column, BigInteger, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.sql import func

# Load .env from the root directory
load_dotenv()

# Database Connection
DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASS')
DB_HOST = os.getenv('DB_HOST')
DB_NAME = os.getenv('DB_NAME')

if not all([DB_USER, DB_PASS, DB_HOST, DB_NAME]):
    raise RuntimeError("Missing database environment variables!")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:5432/{DB_NAME}?sslmode=require"
engine = create_engine(DATABASE_URL, connect_args={"connect_timeout": 10})


SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

# Python Models

# User Management 
class Account(Base):
    __tablename__ = "account"
    accountid = Column(BigInteger, primary_key=True) 
    gmail = Column(String(100), unique=True, nullable=False)
    account_role = Column(String(255), default="user")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class UserSession(Base):
    __tablename__ = "user_sessions"
    session_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    gmail = Column(String, ForeignKey("account.gmail"), nullable=False)
    name = Column(String,   nullable=False)
    picture = Column(String,   nullable=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# Content Storage 
class Article(Base):
    __tablename__ = "article"
    articleid = Column(BigInteger, primary_key=True)
    title = Column(Text)
    content = Column(Text) # This stores 'original-text'
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# NLP Analysis Results
class Summary(Base):
    __tablename__ = "summary"
    summaryid = Column(BigInteger, primary_key=True)
    accountid = Column(BigInteger, ForeignKey("account.accountid"))
    articleid = Column(BigInteger, ForeignKey("article.articleid"))
    summarytext = Column(Text)

class AnalysisResult(Base):
    """Stores the Relationship Map and Ranked Entities"""
    __tablename__ = "analysis_result"
    resultid = Column(BigInteger, primary_key=True)
    articleid = Column(BigInteger, ForeignKey("article.articleid"))
    entities_all_json = Column(Text)
    # rankings_json stores the list of dicts: [{'name': '...', 'distance': 0.1}, ...]
    rankings_json = Column(Text) 
    graph_html = Column(Text)

# User Interactions
class Annotation(Base):
    __tablename__ = "annotation"
    annotationid = Column(BigInteger, primary_key=True)
    accountid = Column(BigInteger, ForeignKey("account.accountid"))
    articleid = Column(BigInteger, ForeignKey("article.articleid"))
    note = Column(Text)

# Initialization logic
def init_db():
    """Verify and sync tables with Azure"""
    try:
        Base.metadata.create_all(bind=engine)
        print("Database Models synced with Azure")
    except Exception as e:
        print(f"Connection/Migration Error: {e}")

if __name__ == "__main__":
    init_db()