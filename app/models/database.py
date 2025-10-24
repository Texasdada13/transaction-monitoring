# app/models/database.py
from sqlalchemy import create_engine, Column, String, Float, ForeignKey, Integer, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import datetime
from config.settings import DATABASE_URL

# Create database engine
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database models
class Account(Base):
    __tablename__ = "accounts"
    
    account_id = Column(String, primary_key=True, index=True)
    creation_date = Column(String, default=lambda: datetime.datetime.utcnow().isoformat())
    risk_tier = Column(String, default="medium")
    status = Column(String, default="active")
    
    # Relationships
    transactions = relationship("Transaction", back_populates="account")
    
class Transaction(Base):
    __tablename__ = "transactions"
    
    transaction_id = Column(String, primary_key=True, index=True)
    timestamp = Column(String, default=lambda: datetime.datetime.utcnow().isoformat())
    account_id = Column(String, ForeignKey("accounts.account_id"))
    counterparty_id = Column(String, index=True)
    amount = Column(Float)
    direction = Column(String, default="credit")  # "credit" (incoming) or "debit" (outgoing)
    transaction_type = Column(String)  # "ACH", "WIRE", etc.
    description = Column(Text, nullable=True)
    tx_metadata = Column(Text, nullable=True)  # JSON string
    
    # Relationships
    account = relationship("Account", back_populates="transactions")
    risk_assessment = relationship("RiskAssessment", back_populates="transaction", uselist=False)
    
class RiskAssessment(Base):
    __tablename__ = "risk_assessments"
    
    assessment_id = Column(String, primary_key=True, index=True)
    transaction_id = Column(String, ForeignKey("transactions.transaction_id"))
    risk_score = Column(Float)
    triggered_rules = Column(Text)  # JSON string of rule names
    decision = Column(String)  # "auto_approve", "manual_review"
    review_status = Column(String, default="pending")  # "pending", "approved", "rejected"
    review_notes = Column(Text, nullable=True)
    review_timestamp = Column(String)
    reviewer_id = Column(String, nullable=True)
    
    # Relationships
    transaction = relationship("Transaction", back_populates="risk_assessment")

# Create all tables
def init_db():
    Base.metadata.create_all(bind=engine)

# Get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()