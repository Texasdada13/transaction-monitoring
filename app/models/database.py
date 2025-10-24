# app/models/database.py
from sqlalchemy import create_engine, Column, String, Float, ForeignKey, Integer, Text, Boolean
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
    employees = relationship("Employee", back_populates="account")
    account_changes = relationship("AccountChangeHistory", back_populates="account")
    
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
    tx_metadata = Column(Text, nullable=True)  # JSON string (renamed from 'metadata' to avoid SQLAlchemy conflict)

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

class Employee(Base):
    __tablename__ = "employees"

    employee_id = Column(String, primary_key=True, index=True)
    account_id = Column(String, ForeignKey("accounts.account_id"))
    name = Column(String)
    email = Column(String, index=True)
    department = Column(String, nullable=True)
    hire_date = Column(String, default=lambda: datetime.datetime.utcnow().isoformat())
    employment_status = Column(String, default="active")  # "active", "terminated", "suspended"

    # Payroll information
    payroll_account_number = Column(String)  # Bank account for payroll
    payroll_routing_number = Column(String)
    payroll_bank_name = Column(String, nullable=True)
    payroll_frequency = Column(String, default="biweekly")  # "weekly", "biweekly", "monthly"
    last_payroll_date = Column(String, nullable=True)

    # Relationships
    account = relationship("Account", back_populates="employees")
    account_changes = relationship("AccountChangeHistory", back_populates="employee")

class AccountChangeHistory(Base):
    __tablename__ = "account_change_history"

    change_id = Column(String, primary_key=True, index=True)
    employee_id = Column(String, ForeignKey("employees.employee_id"), index=True)
    account_id = Column(String, ForeignKey("accounts.account_id"))
    timestamp = Column(String, default=lambda: datetime.datetime.utcnow().isoformat())

    # Change details
    change_type = Column(String)  # "account_number", "routing_number", "bank_name", "email", "phone"
    old_value = Column(String, nullable=True)
    new_value = Column(String)

    # Change metadata
    change_source = Column(String)  # "employee_portal", "hr_system", "phone_request", "email_request"
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    verification_method = Column(String, nullable=True)  # "2fa", "email_confirmation", "phone_call", "none"
    verified = Column(Boolean, default=False)
    verified_by = Column(String, nullable=True)  # HR staff ID
    verification_timestamp = Column(String, nullable=True)

    # Risk indicators
    flagged_as_suspicious = Column(Boolean, default=False)
    suspicious_reason = Column(Text, nullable=True)

    # Relationships
    employee = relationship("Employee", back_populates="account_changes")
    account = relationship("Account", back_populates="account_changes")

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