import re
from datetime import datetime

from airflow.exceptions import AirflowFailException
from pymongo import MongoClient, UpdateOne

# ================== MONGODB CONFIG ==================
CONNECTION_STRING = (
    "mongodb+srv://yashwantharavanti_zintlr:"
    "kdLyBldFohW9dYI6@cluster0.ebb7yqo.mongodb.net/"
)
DB_NAME = "zintlr"

RAW_COLLECTION = "companies_raw"
CLEAN_COLLECTION = "companies_cleaned"

client = MongoClient(CONNECTION_STRING, serverSelectionTimeoutMS=5000)
db = client[DB_NAME]

raw_col = db[RAW_COLLECTION]
clean_col = db[CLEAN_COLLECTION]

# Ensure CIN uniqueness
clean_col.create_index("cin", unique=True)
# ===================================================


# ================== CLEANING UTILITIES ==================
def clean_string(value):
    if value is None:
        return None
    return re.sub(r"\s+", " ", str(value)).strip() or None


def parse_date(value):
    """
    Converts date string into datetime.
    Zauba usually uses DD/MM/YYYY.
    """
    if not value:
        return None

    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue

    return None


def extract_years(age_str):
    """
    Extracts years from:
    '23 years, 5 months, 10 days'
    """
    if not age_str:
        return None

    match = re.search(r"(\d+)\s+years?", age_str)
    return int(match.group(1)) if match else None


def safe_int(value):
    """
    Handles:
    - commas
    - currency symbols
    - text noise
    """
    if not value:
        return None

    try:
        cleaned = re.sub(r"[^\d]", "", str(value))
        return int(cleaned) if cleaned else None
    except Exception:
        return None
# ===================================================


# ================== TRANSFORMATION ==================
def transform_document(doc):
    raw = doc.get("raw_data", {})

    cleaned = {
        # ===== Mandatory (assignment) =====
        "cin": clean_string(raw.get("CIN")),
        "name": clean_string(raw.get("Name")),
        "company_status": clean_string(raw.get("Company Status")),
        "date_of_incorporation": parse_date(
            raw.get("Date of Incorporation")
        ),

        # ===== Optional core fields =====
        "listed_status": clean_string(
            raw.get("Listed on Stock Exchange")
        ),
        "roc": clean_string(raw.get("ROC")),
        "registration_number": safe_int(
            raw.get("Registration Number")
        ),
        "company_category": clean_string(
            raw.get("Company Category")
        ),
        "company_sub_category": clean_string(
            raw.get("Company Sub Category")
        ),
        "company_class": clean_string(
            raw.get("Class of Company")
        ),

        # ===== Financials =====
        "authorized_capital": safe_int(
            raw.get("Authorized Capital")
        ),
        "paid_up_capital": safe_int(
            raw.get("Paid-up Capital")
        ),

        # ===== Industry =====
        "company_age_years": extract_years(
            raw.get("Age of Company")
        ),
        "nic_code": safe_int(raw.get("NIC Code")),
        "nic_description": clean_string(
            raw.get("NIC Description")
        ),
        "number_of_members": safe_int(
            raw.get("Number of Members")
        ),

        # ===== Metadata =====
        "source_url": doc.get("source_url"),
        "scraped_at": doc.get("scraped_at"),
        "cleaned_at": datetime.utcnow(),
    }

    return cleaned
# ===================================================


# ================== AIRFLOW ENTRYPOINT ==================
def clean_pipeline():
    """
    Airflow task entrypoint
    Reads raw data and upserts cleaned records
    """

    total_docs = raw_col.count_documents({})
    print(f"🔹 Raw documents found: {total_docs}")

    if total_docs == 0:
        raise AirflowFailException("No raw documents found to clean")

    operations = []
    skipped = 0

    cursor = raw_col.find(
        {},
        {
            "raw_data": 1,
            "source_url": 1,
            "scraped_at": 1,
        }
    ).sort("scraped_at", 1)

    for doc in cursor:
        cleaned_doc = transform_document(doc)

        # ===== Mandatory validation =====
        if (
            not cleaned_doc.get("cin")
            or not cleaned_doc.get("name")
            or not cleaned_doc.get("company_status")
            or not cleaned_doc.get("date_of_incorporation")
        ):
            skipped += 1
            continue

        operations.append(
            UpdateOne(
                {"cin": cleaned_doc["cin"]},
                {"$set": cleaned_doc},
                upsert=True,
            )
        )

    if not operations:
        raise AirflowFailException(
            "No valid documents after cleaning"
        )

    result = clean_col.bulk_write(operations)

    print("\n================ CLEANING SUMMARY ================")
    print(f"🧾 Raw documents        : {total_docs}")
    print(f"🧹 Cleaned (upserts)    : {len(operations)}")
    print(f"⚠️ Skipped invalid docs : {skipped}")
    print(f"🆕 Inserted             : {len(result.upserted_ids)}")
    print(f"♻️ Updated              : {result.modified_count}")

    print("✅ Cleaning pipeline completed successfully")
