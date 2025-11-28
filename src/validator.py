import os
import xmlschema
from lxml import etree

def validate_xml(xml_string, schema_filename):
    # Construire le chemin vers le dossier schemas
    base_path = os.path.join(os.path.dirname(__file__), "..", "schemas")
    schema_path = os.path.join(base_path, schema_filename)

    try:
        # Charger le schéma directement
        schema = xmlschema.XMLSchema(schema_path)

        # Valider le XML
        schema.validate(etree.fromstring(xml_string.encode("utf-8")))
        return True, f" XML is valid according to {schema_filename}"
    except xmlschema.validators.exceptions.XMLSchemaValidationError as e:
        return False, f" Validation error: {e}"
    except FileNotFoundError as e:
        return False, f" Schema file not found: {schema_path}"