import json
import datetime
from transform import json_to_xml
from crypto import generate_hash, get_timestamp
from validator import validate_xml
from database import init_db, session, Issuer, Recipient, Invoice, Cryptography, TransmissionLog

def main():
    # Initialiser la base (crée les tables si elles n'existent pas)
    init_db()

    # Charger le JSON
    with open("data/invoice.json", "r", encoding="utf-8") as f:
        invoice_data = json.load(f)

    # Générer hash et timestamp
    hash_value = generate_hash(invoice_data)
    timestamp = get_timestamp()

    # Transformer JSON → XML
    xml_string = json_to_xml("data/invoice.json")
    print("=== Generated XML ===")
    print(xml_string)

    # Valider le XML
    valid, message = validate_xml(xml_string, "SuministroLR.xsd")
    print("Validation:", message)

    if not valid:
        return

    # --- Vérifier / créer Issuer ---
    issuer = session.query(Issuer).filter_by(tax_id=invoice_data["issuer_nif"]).first()
    if not issuer:
        issuer = Issuer(
            tax_id=invoice_data["issuer_nif"],
            company_name="Entreprise Émettrice",
            address="Rue Exemple 1"
        )
        session.add(issuer)
        session.commit()

    # --- Vérifier / créer Recipient ---
    recipient = session.query(Recipient).filter_by(tax_id=invoice_data["recipient_nif"]).first()
    if not recipient:
        recipient = Recipient(
            tax_id=invoice_data["recipient_nif"],
            company_name="Client Destinataire",
            address="Rue Client 2"
        )
        session.add(recipient)
        session.commit()

    # --- Créer la facture ---
    invoice = Invoice(
        series_number=invoice_data["invoice_number"],
        issue_date=datetime.datetime.strptime(invoice_data["invoice_date"], "%Y-%m-%d").date(),
        invoice_type="F1",
        taxable_base=invoice_data["amount_base"],
        vat_rate=invoice_data["vat_rate"],
        vat_amount=invoice_data["vat_amount"],
        total_amount=invoice_data["total_amount"],
        issuer_id=issuer.issuer_id,
        recipient_id=recipient.recipient_id
    )
    session.add(invoice)
    session.commit()

    # --- Ajouter cryptographie ---
    crypto = Cryptography(
        invoice_id=invoice.invoice_id,
        sha256_hash=hash_value,
        previous_hash="0000...0000",
        timestamp=timestamp
    )
    session.add(crypto)

    # --- Ajouter transmission log ---
    journal = TransmissionLog(
        invoice_id=invoice.invoice_id,
        status="SENT",
        response_message="AEAT simulation response"
    )
    session.add(journal)

    session.commit()
    print(f" Invoice {invoice.series_number} inserted with ID {invoice.invoice_id}")

if __name__ == "__main__":
    main()