
import os
import pickle
from datetime import datetime
from backend import db_execute
from databases import DBClass


# Main tender sources to pack for model training.
TENDER_TABLES = [
    "federal_table",
    "punjab_table",
    "sindh_table",
    "kpk_table",
    "ajk_table",
    "gilgit_table",
    "balochistan_table",
]

OUTPUT_DIR = os.path.join("files", "training")
LATEST_OUTPUT = os.path.join(OUTPUT_DIR, "tenders_latest.pkl")


def _table_columns(table_name):
    db_map = DBClass.databases_["tenderwala"]
    table_info = db_map.get(table_name)
    if table_info is None:
        return None
    return table_info.get("columns", [])


def _fetch_rows(table_name):
    payload = {
        "db": "tenderwala",
        "table": table_name,
        "cols": None,
        "ops": "SELECT",
        "where": None,
        "value": None,
    }
    return db_execute(payload)


def _rows_to_dicts(table_name, rows):
    columns = _table_columns(table_name) or []
    packed = []

    for row in rows:
        if isinstance(row, dict):
            packed.append(row)
            continue

        if isinstance(row, (list, tuple)):
            item = {}
            for idx, col in enumerate(columns):
                item[col] = row[idx] if idx < len(row) else None
            packed.append(item)
            continue

        packed.append({"value": row})

    return packed


def _province_name(table_name):
    return str(table_name).replace("_table", "").replace("_", " ").title()


def _build_search_record(table_name, row):
    if not isinstance(row, dict):
        return None

    title = str(row.get("title", "") or "").strip()
    category = str(row.get("category", "") or "").strip()
    city = str(row.get("city", "") or "").strip()
    department = str(row.get("department", "") or "").strip()
    tender_type = str(row.get("type", "") or "").strip()
    date_published = str(row.get("date_published", "") or "").strip()
    date_opening = str(row.get("date_opening", "") or "").strip()
    document = str(row.get("document", "") or "").strip()
    estimated_cost = str(row.get("estimated_cost", "") or "").strip()
    province_name = _province_name(table_name)

    return {
        "id": str(row.get("id", "") or "").strip(),
        "table": table_name,
        "province_name": province_name,
        "title": title,
        "category": category,
        "city": city,
        "department": department,
        "type": tender_type,
        "date_published": date_published,
        "date_opening": date_opening,
        "document": document,
        "estimated_cost": estimated_cost,
        "search_text": " | ".join([
            title,
            category,
            city,
            department,
            tender_type,
            province_name
        ]).strip(" |")
    }


def build_tenders_pkl(output_path=LATEST_OUTPUT):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    run_time = datetime.now()
    snapshot = {
        "generated_at": run_time.strftime("%Y-%m-%d %H:%M:%S"),
        "tables": {},
        "records": [],
        "counts": {},
        "errors": {},
    }

    for table_name in TENDER_TABLES:
        result = _fetch_rows(table_name)
        if result.get("status"):
            rows = result.get("data", [])
            packed_rows = _rows_to_dicts(table_name, rows)
            snapshot["tables"][table_name] = packed_rows
            snapshot["counts"][table_name] = len(packed_rows)
            for row in packed_rows:
                record = _build_search_record(table_name, row)
                if record is not None:
                    snapshot["records"].append(record)
        else:
            snapshot["tables"][table_name] = []
            snapshot["counts"][table_name] = 0
            snapshot["errors"][table_name] = str(result)

    timestamp_name = f"tenders_{run_time.strftime('%Y%m%d_%H%M%S')}.pkl"
    timestamp_path = os.path.join(os.path.dirname(output_path), timestamp_name)

    with open(output_path, "wb") as fp:
        pickle.dump(snapshot, fp, protocol=pickle.HIGHEST_PROTOCOL)

    with open(timestamp_path, "wb") as fp:
        pickle.dump(snapshot, fp, protocol=pickle.HIGHEST_PROTOCOL)

    str_ = f"""Train tenders export completed\n
    Latest file: {output_path}\n
    Snapshot file: {timestamp_path}\n
    Counts: {snapshot['counts']}"""
    if len(snapshot["errors"]) > 0:
        str_ = f"Errors: {snapshot['errors']}"

    return str_


def main():

    return build_tenders_pkl(output_path="files/tenders_latest.pkl")





