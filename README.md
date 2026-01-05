# 📋 Fincargo Verifactu PoC - Architecture et Documentation

## 🎯 Vue d'ensemble du projet

**Fincargo Verifactu** est une Proof of Concept (PoC) destinée à transformer et valider des **factures en JSON** conformément aux normes de **Veri*factu**, le système de facturation électronique obligatoire en Espagne.

Le projet automatise l'ensemble du processus :
1. **Transformation** JSON → XML (format Verifactu)
2. **Chaînage cryptographique** (blockchain-like)
3. **Validation** contre les schémas XSD officiels
4. **Stockage** en base de données
5. **Transmission** vers le portail de l'AEAT (Agencia Tributaria Española)

---

## 🏗️ Architecture générale

```
┌─────────────────────────────────────────────────────────────┐
│                    DONNÉES D'ENTRÉE (JSON)                   │
│   - Facture (numéro, date, montants)                         │
│   - Émetteur (NIF, raison sociale)                           │
│   - Destinataire (NIF, raison sociale)                       │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
         ┌────────────────────────────────┐
         │  1️⃣  TRANSFORMATION (JSON→XML) │
         │  transform.py                   │
         └────────────────────┬───────────┘
                              │
                              ▼
         ┌────────────────────────────────────────┐
         │  2️⃣  CRYPTOGRAPHIE & CHAÎNAGE         │
         │  crypto.py                             │
         │  - Génération du hash SHA-256          │
         │  - Création de la "huella" (preuve)    │
         │  - Chaînage avec hash précédent        │
         └────────────────────┬───────────────────┘
                              │
                              ▼
         ┌────────────────────────────────┐
         │  3️⃣  VALIDATION XML             │
         │  validator.py                   │
         │  Vérification contre XSD        │
         └────────────────────┬───────────┘
                              │
                              ▼
         ┌────────────────────────────────┐
         │  4️⃣  STOCKAGE EN BASE DE DONNÉES│
         │  database.py                    │
         │  - Factures                     │
         │  - Cryptographie                │
         │  - Logs de transmission         │
         └────────────────────┬───────────┘
                              │
                              ▼
         ┌────────────────────────────────────┐
         │  5️⃣  TRANSMISSION À L'AEAT        │
         │  (Portail Veri*factu Espagnol)    │
         │  https://www.verifactu.es         │
         └────────────────────────────────────┘
```

---

## 📁 Structure du projet

```
verifactu_poc/
│
├── README.md                      # Cette documentation
├── requirements.txt               # Dépendances Python
├── databaseSchema.sql            # Schéma de la base de données
│
├── src/                          # Code source principal
│   ├── poc_main.py               # Point d'entrée du programme
│   ├── transform.py              # Conversion JSON → XML
│   ├── crypto.py                 # Cryptographie et chaînage
│   ├── validator.py              # Validation XML contre XSD
│   ├── database.py               # Modèles SQLAlchemy
│   ├── mapping.py                # Mappage JSON → champs XML
│   ├── utils.py                  # Utilitaires
│   └── __pycache__/              # Cache Python
│
├── schemas/                      # Schémas XML officiels (AEAT)
│   ├── SuministroInformacion.xsd # Schéma des informations
│   └── SuministroLR.xsd          # Schéma du système facturation
│
├── data/                         # Données de test (factures JSON)
│   ├── invoice.json
│   ├── invoice2.json
│   ├── invoice3.json
│   ├── invoice4.json
│   ├── invoice5.json
│   ├── invoice6.json
│   └── invoice7.json
│
├── xml_output/                   # Fichiers XML générés
│   ├── invoice5.xml
│   ├── invoice6.xml
│   └── invoice7.xml
│
└── tests/                        # Tests unitaires
    ├── test_crypto.py            # Tests cryptographie
    ├── test_transform.py         # Tests transformation
    └── test_validator.py         # Tests validation
```

---

## 🔄 Étapes détaillées de l'architecture

### **Étape 1️⃣ : TRANSFORMATION JSON → XML** (`transform.py`)

**Objectif** : Convertir les données facture du format JSON en XML au format Verifactu de l'AEAT.

**Processus** :
- Lecture du fichier JSON
- Création d'un arborescence XML avec les namespaces officiels AEAT
- Remplissage des éléments XML conformément au schéma `SuministroLR.xsd`
- Formatage des dates (YYYY-MM-DD → DD-MM-YYYY)
- Formatage des montants (2 décimales)
- Injection de métadonnées (timestamp, huella, système informatique)

**Entrée** : `invoice.json`
```json
{
  "invoice_number": "FAC-2025-001",
  "invoice_date": "2025-01-05",
  "issuer": {
    "nombre_razon": "Fincargo SL",
    "nif": "A12345678"
  },
  "recipient": {
    "nombre_razon": "Client SA",
    "nif": "B87654321"
  },
  "amount_base": 1000.00,
  "vat_rate": 21.00,
  "vat_amount": 210.00,
  "total_amount": 1210.00
}
```

**Sortie** : Fichier XML valide au format Verifactu

---

### **Étape 2️⃣ : CRYPTOGRAPHIE ET CHAÎNAGE** (`crypto.py`)

**Objectif** : Assurer l'intégrité des factures et créer une traçabilité (chaînage).

**Processus** :

#### A. **Génération du Hash SHA-256** (`generate_hash()`)
- Convertir le JSON en chaîne canonique (clés triées)
- Encoder en UTF-8
- Calculer le hash SHA-256

#### B. **Récupération du Hash Précédent** (`get_previous_hash()`)
- Consulter la base de données
- Récupérer le hash SHA-256 de la **dernière facture**
- Si aucune facture : initialiser à 64 zéros (`0000...`)
- Cela crée un **chaînage** : chaque facture référence la précédente

#### C. **Construction de la "Huella"** (`compute_huella()`)
- Combiner le hash précédent + données clés de la facture
- Créer une chaîne canonique :
  ```
  [previous_hash] + [NIF émetteur] + [numéro facture] + [date] + 
  [base imposable] + [taux TVA] + [montant TVA]
  ```
- Calculer le hash SHA-256 de cette combinaison
- Cette "huella" (empreinte) est **inscrite dans le XML** et servira de **preuve d'intégrité**

#### D. **Timestamp ISO 8601** (`get_timestamp()`)
- Enregistrer la date/heure exacte de génération
- Format : `2025-01-05T14:32:45.123456`

**Résultat** :
- ✅ Chaque facture a une empreinte unique
- ✅ Impossible de modifier une facture sans casser le chaînage
- ✅ Traçabilité complète : facture N → facture N-1 → facture N-2...

---

### **Étape 3️⃣ : VALIDATION XML** (`validator.py`)

**Objectif** : Vérifier que le XML généré respecte les normes officielles AEAT.

**Processus** :
- Charger le schéma XSD officiel (`SuministroLR.xsd`)
- Valider le XML généré contre le schéma
- Retourner True/False + message d'erreur détaillé

**Schémas utilisés** :
- `SuministroLR.xsd` : Définit la structure complète d'une facture Verifactu
- `SuministroInformacion.xsd` : Schéma des éléments d'information

**Erreurs courantes** :
- ❌ Éléments manquants (obligatoires)
- ❌ Format de date incorrect
- ❌ Montants avec mauvais nombre de décimales
- ❌ NIF invalide
- ❌ Namespaces incorrects

---

### **Étape 4️⃣ : STOCKAGE EN BASE DE DONNÉES** (`database.py`)

**Objectif** : Persister les factures, les données cryptographiques et les logs.

**Modèle de données** :

```
┌─────────────────┐
│    ISSUER       │  ← Émetteur (entreprise qui facture)
│  (issuer_id)    │
│  - tax_id (NIF) │
│  - company_name │
│  - address      │
└────────┬────────┘
         │ (1:N)
         │
┌────────┴──────────┬──────────────────┐
│                   │                  │
▼                   ▼                  ▼
INVOICE         CRYPTOGRAPHY      TRANSMISSION_LOG
(invoice_id)    (crypto_id)       (log_id)
- series_number - sha256_hash     - send_date
- issue_date    - previous_hash   - status
- invoice_type  - timestamp       - response_message
- amounts       - digital_sig...
- recipient_id  - invoice_id (FK)
- issuer_id (FK)
                     │
                     └─ Référence la facture
                        pour traçabilité
```

**Tables principales** :

1. **issuer** : Entreprises émettrices
2. **recipient** : Destinataires/clients
3. **invoice** : Factures (montants, dates, types)
4. **cryptography** : Données de sécurité (hashes, timestamps)
5. **transmission_log** : Historique des envois à l'AEAT

---

### **Étape 5️⃣ : TRANSMISSION À L'AEAT** (Intégration future)

**Objectif** : Envoyer les factures XML au portail officiel Verifactu de l'Agencia Tributaria Española.

**URL du portail** : https://www.verifactu.es

**Processus** (à implémenter) :
1. Récupérer le XML validé de la base de données
2. Signer numériquement le XML (certificat numérique)
3. Envoyer via API REST sécurisée à l'AEAT
4. Enregistrer la réponse (succès/erreur) dans `transmission_log`
5. Stocker la confirmation officielle de l'AEAT

---

## 🔧 Technologies utilisées

| Composant | Technologie | Raison |
|-----------|-------------|--------|
| **Manipulation XML** | `lxml` | Génération et parsing rapide |
| **Validation XML** | `xmlschema` | Conformité stricte aux XSD |
| **Cryptographie** | `cryptography` | Hash SHA-256, signatures |
| **Base de données** | `SQLAlchemy` | ORM flexible (PostgreSQL/MySQL/SQLite) |
| **Tests** | `pytest` | Framework de test robuste |
| **Environnement** | `python-dotenv` | Gestion des variables de configuration |

---

## 🚀 Guide d'utilisation

### Installation
```bash
pip install -r requirements.txt
```

### Exécution principale
```bash
python src/poc_main.py data/invoice.json
```

### Tests unitaires
```bash
pytest tests/
```

---

## 📊 Flux complet d'une facture

```
1. Invoice.json ──────────┐
                          │
2. Transform (JSON→XML)   │
   ├─ Normalisation dates │
   ├─ Formatage montants  │
   └─ Injection metadata  │
                          ▼
3. Crypto ────────────────┐
   ├─ SHA256 hash         │
   ├─ Previous hash       │
   └─ Huella computation  │
                          ▼
4. XML complet + huella ──┐
                          │
5. Validation XSD ────────┤
   ├─ Structure OK?       │
   ├─ Formats OK?         │
   └─ Valeurs OK?         │
                          ▼
6. Store in Database ─────┐
   ├─ Invoice record      │
   ├─ Crypto record       │
   └─ Status logs         │
                          ▼
7. Ready for AEAT ────────┐
   ├─ Sign XML (cert)     │
   └─ Send via API        │
                          ▼
8. Confirmation AEAT ─────┐
   └─ Store response      │
```

---

## ✅ Conformité Veri*factu

Ce projet respecte les normes officielles du système Verifactu :

- ✅ **Schémas XSD** de l'AEAT
- ✅ **Chaînage des hashes** (intégrité)
- ✅ **Horodatage** (timestamps ISO 8601)
- ✅ **Format de facture** (F1, R1, F2, R2, etc.)
- ✅ **Identification du système informatique**
- ✅ **Destinataires multiples** (si applicable)
- ✅ **Support représentants fiscaux**

---

## 🔐 Sécurité

1. **Chaînage cryptographique** : Chaque facture est liée à la précédente
2. **Hash SHA-256** : Impossible de modifier sans détection
3. **Validation stricte** : Rejet des factures non-conformes
4. **Logs de transmission** : Traçabilité complète des envois
5. **Base de données** : Audit trail pour compliance

---

## 📝 Mappage JSON → XML

Le fichier `mapping.py` contient les correspondances entre les champs JSON et les chemins XML Verifactu :

```python
MAPPING = {
    "invoice_number": "IDFactura/NumSerieFactura",
    "invoice_date": "IDFactura/FechaExpedicionFactura",
    "issuer_nombre_razon": "ObligadoEmision/NombreRazon",
    "issuer_nif": "ObligadoEmision/NIF",
    "recipient_nombre_razon": "Destinatarios/IDDestinatario/NombreRazon",
    # ... etc
}
```

---

## 🐛 Dépannage

| Erreur | Cause | Solution |
|--------|-------|----------|
| `XMLSchemaValidationError` | XML ne respecte pas le schéma | Vérifier les formats de date/montants, éléments obligatoires |
| `FileNotFoundError: schema_path` | Schéma XSD manquant | Vérifier que `schemas/` existe et contient les fichiers XSD |
| `Cryptography.IntegrityError` | Chaînage rompu | Vérifier que la base n'a pas été modifiée |
| `psycopg2.OperationalError` | DB non accessible | Vérifier la connexion PostgreSQL |

---

## 📚 Ressources officielles

- **Portail Veri*factu** : https://www.verifactu.es
- **Documentation AEAT** : https://www.agenciatributaria.gob.es
- **Schémas XSD** : https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/
- **Spécifications techniques** : https://www.agenciatributaria.gob.es/AEAT.internet/Inicio/Inicio.shtml

---

## 👥 Auteurs et maintenance

**Projet** : Fincargo Verifactu PoC  
**Repository** : `fincargo-invoice-parser` (branch: `verifactu`)  
**Propriétaire** : DTA-2023

---

## 📌 Notes de version

**Version 1.0.0** (PoC)
- ✅ Transformation JSON → XML
- ✅ Génération hashes et chaînage
- ✅ Validation XSD
- ✅ Stockage en base de données
- ⏳ Signature numérique (planifiée)
- ⏳ Transmission AEAT (planifiée)
- ⏳ Interface web (planifiée)

---

**Dernière mise à jour** : 5 janvier 2026
