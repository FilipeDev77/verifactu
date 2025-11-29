import json
from lxml import etree

def normalize_date(date_str: str) -> str:
    """YYYY-MM-DD -> DD-MM-YYYY"""
    y, m, d = date_str.split("-")
    return f"{d}-{m}-{y}"

def format_importe(value: float) -> str:
    """Format montant avec 2 décimales"""
    return f"{value:.2f}"

def format_tipo(value: float) -> str:
    """Format taux TVA"""
    return f"{value:.2f}"

def json_to_xml(json_file: str, *, huella: str, fecha_hora_iso: str) -> str:
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    nsmap = {
        "sfLR": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroLR.xsd",
        "sf": "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd"
    }

    root = etree.Element(f"{{{nsmap['sfLR']}}}RegFactuSistemaFacturacion", nsmap=nsmap)

    # Cabecera
    cabecera = etree.SubElement(root, f"{{{nsmap['sfLR']}}}Cabecera")
    obligado = etree.SubElement(cabecera, f"{{{nsmap['sf']}}}ObligadoEmision")
    etree.SubElement(obligado, f"{{{nsmap['sf']}}}NombreRazon").text = data["issuer"]["nombre_razon"]
    etree.SubElement(obligado, f"{{{nsmap['sf']}}}NIF").text = data["issuer"]["nif"]

    if "representante" in data:
        rep = etree.SubElement(cabecera, f"{{{nsmap['sf']}}}Representante")
        etree.SubElement(rep, f"{{{nsmap['sf']}}}NombreRazon").text = data["representante"]["nombre_razon"]
        etree.SubElement(rep, f"{{{nsmap['sf']}}}NIF").text = data["representante"]["nif"]

    # RegistroFactura -> RegistroAlta
    registro_factura = etree.SubElement(root, f"{{{nsmap['sfLR']}}}RegistroFactura")
    registro_alta = etree.SubElement(registro_factura, f"{{{nsmap['sf']}}}RegistroAlta")

    etree.SubElement(registro_alta, f"{{{nsmap['sf']}}}IDVersion").text = "1.0"

    id_factura = etree.SubElement(registro_alta, f"{{{nsmap['sf']}}}IDFactura")
    etree.SubElement(id_factura, f"{{{nsmap['sf']}}}IDEmisorFactura").text = data["issuer"]["nif"]
    etree.SubElement(id_factura, f"{{{nsmap['sf']}}}NumSerieFactura").text = data["invoice_number"]
    etree.SubElement(id_factura, f"{{{nsmap['sf']}}}FechaExpedicionFactura").text = normalize_date(data["invoice_date"])

    etree.SubElement(registro_alta, f"{{{nsmap['sf']}}}NombreRazonEmisor").text = data["issuer"]["nombre_razon"]

    tipo_factura = data.get("tipo_factura", "F1")
    etree.SubElement(registro_alta, f"{{{nsmap['sf']}}}TipoFactura").text = tipo_factura

    etree.SubElement(registro_alta, f"{{{nsmap['sf']}}}DescripcionOperacion").text = "Venta de bienes/servicios"

    destinatarios = etree.SubElement(registro_alta, f"{{{nsmap['sf']}}}Destinatarios")
    id_dest = etree.SubElement(destinatarios, f"{{{nsmap['sf']}}}IDDestinatario")
    etree.SubElement(id_dest, f"{{{nsmap['sf']}}}NombreRazon").text = data["recipient"]["nombre_razon"]
    etree.SubElement(id_dest, f"{{{nsmap['sf']}}}NIF").text = data["recipient"]["nif"]

    desglose = etree.SubElement(registro_alta, f"{{{nsmap['sf']}}}Desglose")
    detalle = etree.SubElement(desglose, f"{{{nsmap['sf']}}}DetalleDesglose")
    etree.SubElement(detalle, f"{{{nsmap['sf']}}}Impuesto").text = "01"
    etree.SubElement(detalle, f"{{{nsmap['sf']}}}CalificacionOperacion").text = "S1"
    etree.SubElement(detalle, f"{{{nsmap['sf']}}}TipoImpositivo").text = format_tipo(float(data["vat_rate"]))
    etree.SubElement(detalle, f"{{{nsmap['sf']}}}BaseImponibleOimporteNoSujeto").text = format_importe(float(data["amount_base"]))
    etree.SubElement(detalle, f"{{{nsmap['sf']}}}CuotaRepercutida").text = format_importe(float(data["vat_amount"]))

    etree.SubElement(registro_alta, f"{{{nsmap['sf']}}}CuotaTotal").text = format_importe(float(data["vat_amount"]))
    etree.SubElement(registro_alta, f"{{{nsmap['sf']}}}ImporteTotal").text = format_importe(float(data["total_amount"]))

    enc = etree.SubElement(registro_alta, f"{{{nsmap['sf']}}}Encadenamiento")
    etree.SubElement(enc, f"{{{nsmap['sf']}}}PrimerRegistro").text = "S"

    si = etree.SubElement(registro_alta, f"{{{nsmap['sf']}}}SistemaInformatico")
    etree.SubElement(si, f"{{{nsmap['sf']}}}NombreRazon").text = data["issuer"]["nombre_razon"]
    etree.SubElement(si, f"{{{nsmap['sf']}}}NIF").text = data["issuer"]["nif"]
    etree.SubElement(si, f"{{{nsmap['sf']}}}NombreSistemaInformatico").text = "Fincargo-Verifactu"
    etree.SubElement(si, f"{{{nsmap['sf']}}}IdSistemaInformatico").text = "FC"
    etree.SubElement(si, f"{{{nsmap['sf']}}}Version").text = "1.0.0"
    etree.SubElement(si, f"{{{nsmap['sf']}}}NumeroInstalacion").text = "INST-001"
    etree.SubElement(si, f"{{{nsmap['sf']}}}TipoUsoPosibleSoloVerifactu").text = "N"
    etree.SubElement(si, f"{{{nsmap['sf']}}}TipoUsoPosibleMultiOT").text = "S"
    etree.SubElement(si, f"{{{nsmap['sf']}}}IndicadorMultiplesOT").text = "N"

    etree.SubElement(registro_alta, f"{{{nsmap['sf']}}}FechaHoraHusoGenRegistro").text = fecha_hora_iso
    etree.SubElement(registro_alta, f"{{{nsmap['sf']}}}TipoHuella").text = "01"
    etree.SubElement(registro_alta, f"{{{nsmap['sf']}}}Huella").text = huella

    return etree.tostring(root, pretty_print=True, encoding="utf-8").decode("utf-8")