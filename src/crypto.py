import hashlib
import datetime
import json
from database import session, Cryptography

def generate_hash(data):
    """
    Génère un hash SHA256 à partir du JSON brut (trié).
    """
    raw_string = json.dumps(data, sort_keys=True).encode("utf-8")
    return hashlib.sha256(raw_string).hexdigest()

def get_timestamp():
    """
    Retourne un timestamp ISO 8601.
    """
    return datetime.datetime.now().isoformat()

def get_previous_hash():
    """
    Retourne le hash de la dernière facture insérée (chaînage Veri*factu).
    Si aucune facture n'existe : renvoie 64 zéros.
    """
    last_crypto = session.query(Cryptography)\
                         .order_by(Cryptography.crypto_id.desc())\
                         .first()
    return last_crypto.sha256_hash if last_crypto else "0" * 64

def build_canonical_string(invoice_data: dict, previous_hash: str) -> str:
    """
    Construit une chaîne canonique à partir des champs clés de la facture
    et du hash précédent pour le chaînage Veri*factu.
    """
    parts = [
        previous_hash,
        invoice_data["issuer"]["nif"],
        invoice_data["invoice_number"],
        invoice_data["invoice_date"],
        str(invoice_data["amount_base"]),
        str(invoice_data["vat_rate"]),
        str(invoice_data["vat_amount"]),
        str(invoice_data["total_amount"])
    ]
    return "|".join(parts)

def compute_huella(invoice_data: dict, previous_hash: str) -> str:
    """
    Calcule la huella SHA256 à partir de la chaîne canonique.
    """
    canonical = build_canonical_string(invoice_data, previous_hash)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

def store_crypto(invoice_id, sha256_hash, timestamp):
    """
    Enregistre la cryptographie (hash brut + previous_hash + timestamp) en BDD.
    """
    previous_hash = get_previous_hash()
    crypto = Cryptography(
        invoice_id=invoice_id,
        sha256_hash=sha256_hash,
        previous_hash=previous_hash,
        timestamp=timestamp
    )
    session.add(crypto)
    session.commit()
    return crypto