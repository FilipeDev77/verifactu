import hashlib
import datetime
import json

def generate_hash(data):
    raw_string = json.dumps(data, sort_keys=True).encode("utf-8")
    return hashlib.sha256(raw_string).hexdigest()

def get_timestamp():
    return datetime.datetime.now().isoformat()