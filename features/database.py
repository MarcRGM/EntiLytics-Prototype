import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, Column, BigInteger, String, Text, ForeignKey, Float, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.sql import func

# Load .env from the root directory
load_dotenv()

# Database Connection
DATABASE_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:5432/{os.getenv('DB_NAME')}?sslmode=require"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

# PYTHON MODELS
class Account(Base):
    __tablename__ = "account"  # PostgreSQL maps to lowercase by default
    AccountID = Column(BigInteger, primary_key=True)
    Gmail = Column(String(100), unique=True, nullable=False)
    Account_Role = Column(String(255), default="user")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Article(Base):
    __tablename__ = "article"
    ArticleID = Column(BigInteger, primary_key=True)
    Title = Column(Text)
    Content = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Summary(Base):
    __tablename__ = "summary"
    SummaryID = Column(BigInteger, primary_key=True)
    AccountID = Column(BigInteger, ForeignKey("account.AccountID"))
    ArticleID = Column(BigInteger, ForeignKey("article.ArticleID"))
    SummaryText = Column(Text)

class Annotation(Base):
    __tablename__ = "annotation"
    AnnotationID = Column(BigInteger, primary_key=True)
    AccountID = Column(BigInteger, ForeignKey("account.AccountID"))
    ArticleID = Column(BigInteger, ForeignKey("article.ArticleID"))
    Note = Column(Text)

# Schema initialization logic
def init_db():
    """Verify tables exist"""
    # Ensure everything is synced
    try:
        # This will create tables if they don't exist
        Base.metadata.create_all(bind=engine)
        print("Database Models synced and verified with Azure Japan West.")
    except Exception as e:
        print(f"Connection/Migration Error: {e}")

if __name__ == "__main__":
    init_db()