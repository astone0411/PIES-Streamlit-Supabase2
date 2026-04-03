"""
SQLAlchemy models for the LIMS application (Supabase-backed).
"""

from sqlalchemy import (
    create_engine, Column, Integer, String, DateTime,
    Boolean, Text, ForeignKey, Enum
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime
import enum
import os

from urllib.parse import quote_plus

# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------
Base = declarative_base()


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------
class TestResult(str, enum.Enum):
    DETECTED = "Detected"
    NOT_DETECTED = "Not Detected"
    INCONCLUSIVE = "Inconclusive"
    PENDING = "Pending"


class Sex(str, enum.Enum):
    MALE = "Male"
    FEMALE = "Female"
    UNKNOWN = "Unknown"


class QCStatus(str, enum.Enum):
    PENDING = "Pending"
    APPROVED = "Approved"
    REJECTED = "Rejected"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True, nullable=False)
    display_name = Column(String(128), nullable=False)
    password_hash = Column(String(256), nullable=False)
    role = Column(String(32), default="technician")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    audit_logs = relationship("AuditLog", back_populates="user")
    qc_signoffs = relationship("QCRecord", back_populates="signed_by_user")


class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True)
    external_id = Column(String(64), unique=True, nullable=False)
    first_name = Column(String(128), nullable=False)
    last_name = Column(String(128), nullable=False)
    date_of_birth = Column(String(10), nullable=False)
    sex = Column(Enum(Sex), default=Sex.UNKNOWN)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    specimens = relationship("Specimen", back_populates="patient")


class Specimen(Base):
    __tablename__ = "specimens"

    id = Column(Integer, primary_key=True)
    accession_number = Column(String(64), unique=True, nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)

    source_result = Column(Enum(TestResult), default=TestResult.PENDING)
    collected_at = Column(DateTime)
    received_at = Column(DateTime)

    diagnosis = Column(String(256))
    indication_for_test = Column(Text)
    supplemental_result = Column(Enum(TestResult), default=TestResult.PENDING)
    supplemental_notes = Column(Text)

    entered_by_id = Column(Integer, ForeignKey("users.id"))
    entered_at = Column(DateTime)

    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    patient = relationship("Patient", back_populates="specimens")
    entered_by = relationship("User", foreign_keys=[entered_by_id])
    qc_records = relationship("QCRecord", back_populates="specimen")
    audit_logs = relationship("AuditLog", back_populates="specimen")


class QCRecord(Base):
    __tablename__ = "qc_records"

    id = Column(Integer, primary_key=True)
    specimen_id = Column(Integer, ForeignKey("specimens.id"), nullable=False)
    signed_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    status = Column(Enum(QCStatus), default=QCStatus.PENDING)
    notes = Column(Text)
    signed_at = Column(DateTime, default=datetime.utcnow)

    specimen = relationship("Specimen", back_populates="qc_records")
    signed_by_user = relationship("User", back_populates="qc_signoffs")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    specimen_id = Column(Integer, ForeignKey("specimens.id"))
    action = Column(String(128), nullable=False)
    detail = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="audit_logs")
    specimen = relationship("Specimen", back_populates="audit_logs")


# ---------------------------------------------------------------------------
# Database configuration (Supabase)
# ---------------------------------------------------------------------------

def get_engine():
    """
    Returns a SQLAlchemy engine connected to Supabase via the IPv4 pooler.
    """

    raw_password = os.environ["SUPABASE_DB_PASSWORD"]
    password = quote_plus(raw_password)  # ✅ critical fix

    DATABASE_URL = (
        "postgresql+psycopg://"
        f"postgres.xovmkkshwlluphengwtx:{password}"
        "@aws-1-us-west-1.pooler.supabase.com:6543/postgres"
    )

    return create_engine(
        DATABASE_URL,
        connect_args={"sslmode": "require"},
        pool_pre_ping=True,
    )



# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------
def init_db(engine=None):
    """
    Create tables and seed default users if the users table is empty.
    """
    from database.seed import seed_default_users

    engine = engine or get_engine()
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)

    with Session() as session:
        seed_default_users(session)


def get_session(engine=None):
    engine = engine or get_engine()
    Session = sessionmaker(bind=engine)
    return Session()