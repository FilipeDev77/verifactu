import os

def store_xml(xml_string: str, json_path: str, output_dir: str = "xml_output") -> str:
    """
    Sauvegarde le XML généré dans un fichier .xml.
    Le nom du fichier est basé sur le JSON d'entrée.
    """
    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(json_path))[0]
    xml_path = os.path.join(output_dir, f"{base_name}.xml")

    with open(xml_path, "w", encoding="utf-8") as f:
        f.write(xml_string)

    print(f"XML sauvegardé dans {xml_path}")
    return xml_path