import json
import sys
import datetime
from transform import json_to_xml
from crypto import generate_hash, get_timestamp, store_crypto, get_previous_hash, compute_huella
from validator import validate_xml
from database import init_db, session, Issuer, Recipient, Invoice, TransmissionLog

def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <chemin_fichier_json>")
        return

    json_path = sys.argv[1]
    print("Fichier JSON utilisé :", json_path)

    init_db()

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            invoice_data = json.load(f)
    except FileNotFoundError:
        print("ERREUR : Le fichier", json_path, "n'existe pas.")
        return
    except json.JSONDecodeError:
        print("ERREUR : Le fichier", json_path, "n'est pas un JSON valide.")
        return

    # 4. Générer hash brut et huella
    content_hash = generate_hash(invoice_data)
    previous_hash = get_previous_hash()
    huella = compute_huella(invoice_data, previous_hash)
    timestamp = get_timestamp()

    # 5. Transformer JSON → XML avec huella et timestamp
    xml_string = json_to_xml(json_path, huella=huella, fecha_hora_iso=timestamp)
    print("=== XML généré ===")
    print(xml_string)

    # 6. Valider le XML
    valid, message = validate_xml(xml_string, "SuministroLR.xsd")
    print("Validation :", message)
    if not valid:
        print("XML non valide, arrêt du traitement.")
        return

    # 7. Vérifier / créer Issuer
    issuer_tax_id = invoice_data["issuer"]["nif"]
    issuer_name = invoice_data["issuer"]["nombre_razon"]
    issuer = session.query(Issuer).filter_by(tax_id=issuer_tax_id).first()
    if not issuer:
        issuer = Issuer(tax_id=issuer_tax_id, company_name=issuer_name, address="Rue Exemple 1")
        session.add(issuer)
        session.commit()

    # 8. Vérifier / créer Recipient
    recipient_tax_id = invoice_data["recipient"]["nif"]
    recipient_name = invoice_data["recipient"]["nombre_razon"]
    recipient = session.query(Recipient).filter_by(tax_id=recipient_tax_id).first()
    if not recipient:
        recipient = Recipient(tax_id=recipient_tax_id, company_name=recipient_name, address="Rue Client 2")
        session.add(recipient)
        session.commit()

    # 9. Créer la facture
    invoice = Invoice(
        series_number=invoice_data["invoice_number"],
        issue_date=datetime.datetime.strptime(invoice_data["invoice_date"], "%Y-%m-%d").date(),
        invoice_type=invoice_data.get("tipo_factura", "F1"),
        taxable_base=invoice_data["amount_base"],
        vat_rate=invoice_data["vat_rate"],
        vat_amount=invoice_data["vat_amount"],
        total_amount=invoice_data["total_amount"],
        issuer_id=issuer.issuer_id,
        recipient_id=recipient.recipient_id
    )
    session.add(invoice)
    session.commit()

    # 10. Stocker cryptographie
    store_crypto(invoice.invoice_id, sha256_hash=content_hash, timestamp=timestamp)

    # 11. Journal transmission
    journal = TransmissionLog(
        invoice_id=invoice.invoice_id,
        status="SENT",
        response_message="AEAT simulation response"
    )
    session.add(journal)
    session.commit()

    print("Facture", invoice.series_number, "insérée avec ID", invoice.invoice_id)

if __name__ == "__main__":
    main()