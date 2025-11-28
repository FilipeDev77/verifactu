import json
from lxml import etree

def normalize_date(date_str: str) -> str:
    """
    Convert date from YYYY-MM-DD to DD-MM-YYYY
    """
    parts = date_str.split("-")
    return f"{parts[2]}-{parts[1]}-{parts[0]}"

def normalize_amount(amount: float) -> str:
    """
    Format amount with 15 digits and 2 decimals (VERI*FACTU requirement)
    """
    return f"{amount:015.2f}"

def json_to_xml(json_file: str) -> str:
    """
    Transform JSON invoice into XML VERI*FACTU format
    compliant with SuministroLR.xsd and SuministroInformacion.xsd
    """
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Namespaces
    nsmap = {
        "sfLR": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroLR.xsd",
        "sf": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd"
    }

    # Racine qualifiée avec sfLR
    root = etree.Element(f"{{{nsmap['sfLR']}}}RegFactuSistemaFacturacion", nsmap=nsmap)

    # Cabecera (ordre strict du schéma)
    cabecera = etree.SubElement(root, f"{{{nsmap['sfLR']}}}Cabecera")
    etree.SubElement(cabecera, f"{{{nsmap['sf']}}}IDEmisorFactura").text = str(data["issuer_nif"])
    etree.SubElement(cabecera, f"{{{nsmap['sf']}}}NumSerieFactura").text = str(data["invoice_number"])
    etree.SubElement(cabecera, f"{{{nsmap['sf']}}}FechaExpedicionFactura").text = normalize_date(data["invoice_date"])
    etree.SubElement(cabecera, f"{{{nsmap['sf']}}}IDDestinatarioFactura").text = str(data["recipient_nif"])

    # RegistroFactura
    registro_factura = etree.SubElement(root, f"{{{nsmap['sfLR']}}}RegistroFactura")
    registro_alta = etree.SubElement(registro_factura, f"{{{nsmap['sf']}}}RegistroAlta")

    etree.SubElement(registro_alta, f"{{{nsmap['sf']}}}TipoFactura").text = "F1"
    etree.SubElement(registro_alta, f"{{{nsmap['sf']}}}BaseImponible").text = normalize_amount(float(data["amount_base"]))
    etree.SubElement(registro_alta, f"{{{nsmap['sf']}}}TipoImpositivo").text = normalize_amount(float(data["vat_rate"]))
    etree.SubElement(registro_alta, f"{{{nsmap['sf']}}}CuotaRepercutida").text = normalize_amount(float(data["vat_amount"]))
    etree.SubElement(registro_alta, f"{{{nsmap['sf']}}}ImporteTotal").text = normalize_amount(float(data["total_amount"]))

    return etree.tostring(root, pretty_print=True, encoding="utf-8").decode("utf-8")