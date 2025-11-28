from sqlalchemy import create_engine, Column, Integer, String, Date, DECIMAL, ForeignKey, TIMESTAMP, Text
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
import datetime

Base = declarative_base()

class Issuer(Base):
    __tablename__ = "issuer"
    issuer_id = Column(Integer, primary_key=True)
    tax_id = Column(String(9), unique=True, nullable=False)
    company_name = Column(String(120), nullable=False)
    address = Column(String(255))
    certified_system = Column(String(5), default="FALSE")  # optional flag

class Recipient(Base):
    __tablename__ = "recipient"
    recipient_id = Column(Integer, primary_key=True)
    tax_id = Column(String(9))
    company_name = Column(String(120))
    address = Column(String(255))

class Invoice(Base):
    __tablename__ = "invoice"
    invoice_id = Column(Integer, primary_key=True)
    series_number = Column(String(60), nullable=False)
    issue_date = Column(Date, nullable=False)
    invoice_type = Column(String(3), nullable=False)
    taxable_base = Column(DECIMAL(12,2), nullable=False)
    vat_rate = Column(DECIMAL(5,2), nullable=False)
    vat_amount = Column(DECIMAL(12,2), nullable=False)
    total_amount = Column(DECIMAL(12,2), nullable=False)
    issuer_id = Column(Integer, ForeignKey("issuer.issuer_id"), nullable=False)
    recipient_id = Column(Integer, ForeignKey("recipient.recipient_id"))

class Cryptography(Base):
    __tablename__ = "cryptography"
    crypto_id = Column(Integer, primary_key=True)
    invoice_id = Column(Integer, ForeignKey("invoice.invoice_id"), nullable=False)
    sha256_hash = Column(String(64), nullable=False)
    previous_hash = Column(String(64))
    timestamp = Column(TIMESTAMP, default=datetime.datetime.utcnow)
    digital_signature = Column(Text)

class TransmissionLog(Base):
    __tablename__ = "transmission_log"
    log_id = Column(Integer, primary_key=True)
    invoice_id = Column(Integer, ForeignKey("invoice.invoice_id"), nullable=False)
    send_date = Column(TIMESTAMP, default=datetime.datetime.utcnow)
    status = Column(String(20), nullable=False)
    response_message = Column(Text)

# Database connection (example PostgreSQL)
engine = create_engine("postgresql://postgres:14122002Ne@localhost/verifactu_db")
Session = sessionmaker(bind=engine)
session = Session()

def init_db():
    Base.metadata.create_all(engine)