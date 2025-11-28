-- ================================
-- VERI*FACTU Database Schema (English)
-- ================================

-- Table of issuers (companies sending invoices)
CREATE TABLE issuer (
    issuer_id SERIAL PRIMARY KEY,
    tax_id CHAR(9) NOT NULL UNIQUE,
    company_name VARCHAR(120) NOT NULL,
    address VARCHAR(255),
    certified_system BOOLEAN DEFAULT FALSE
);

-- Table of recipients (clients/customers)
CREATE TABLE recipient (
    recipient_id SERIAL PRIMARY KEY,
    tax_id CHAR(9),
    company_name VARCHAR(120),
    address VARCHAR(255)
);

-- Table of invoices
CREATE TABLE invoice (
    invoice_id SERIAL PRIMARY KEY,
    series_number VARCHAR(60) NOT NULL,
    issue_date DATE NOT NULL,
    invoice_type VARCHAR(3) NOT NULL CHECK (invoice_type IN ('F1','F2','R1','R2','R3','R4','R5','F3')),
    operation_description VARCHAR(500),
    taxable_base DECIMAL(12,2) NOT NULL,
    vat_rate DECIMAL(5,2) NOT NULL,
    vat_amount DECIMAL(12,2) NOT NULL,
    total_amount DECIMAL(12,2) NOT NULL,
    issuer_id INT NOT NULL REFERENCES issuer(issuer_id),
    recipient_id INT REFERENCES recipient(recipient_id)
);

-- Table for cryptographic metadata (traceability)
CREATE TABLE cryptography (
    crypto_id SERIAL PRIMARY KEY,
    invoice_id INT NOT NULL REFERENCES invoice(invoice_id),
    sha256_hash CHAR(64) NOT NULL,
    previous_hash CHAR(64),
    timestamp TIMESTAMP NOT NULL,
    digital_signature TEXT
);

-- Table for certified billing system information
CREATE TABLE billing_system (
    system_id SERIAL PRIMARY KEY,
    system_name VARCHAR(120) NOT NULL,
    version VARCHAR(20) NOT NULL,
    unique_identifier CHAR(2) NOT NULL,
    installation_number VARCHAR(50),
    multi_ot BOOLEAN DEFAULT FALSE
);

-- Table for transmission logs (communication with AEAT)
CREATE TABLE transmission_log (
    log_id SERIAL PRIMARY KEY,
    invoice_id INT NOT NULL REFERENCES invoice(invoice_id),
    send_date TIMESTAMP NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('SENT','VALIDATED','REJECTED')),
    response_message TEXT
);