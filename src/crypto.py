import hashlib
import datetime
import json
from database import session, Cryptography


def generate_hash(data):
    """
    Génère un hash SHA256 à partir d'un dictionnaire JSON.
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
    Retourne le hash de la dernière facture insérée (chaînage Verifactu).
    Si aucune facture n'existe : renvoie 64 zéros.
    """
    last_crypto = session.query(Cryptography)\
                         .order_by(Cryptography.crypto_id.desc())\
                         .first()

    return last_crypto.sha256_hash if last_crypto else "0" * 64


def store_crypto(invoice_id, sha256_hash, timestamp):
    """
    Enregistre la cryptographie (hash + previous_hash + timestamp) en BDD.
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