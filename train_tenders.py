import argparse
import os
import pickle
import time
from datetime import datetime, timedelta

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
    "all_tenders_table",
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


def build_tenders_pkl(output_path=LATEST_OUTPUT):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    run_time = datetime.now()
    snapshot = {
        "generated_at": run_time.strftime("%Y-%m-%d %H:%M:%S"),
        "tables": {},
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

    print("Train tenders export completed")
    print(f"Latest file: {output_path}")
    print(f"Snapshot file: {timestamp_path}")
    print(f"Counts: {snapshot['counts']}")
    if len(snapshot["errors"]) > 0:
        print(f"Errors: {snapshot['errors']}")

    return snapshot


def _seconds_until(hour, minute):
    now = datetime.now()
    next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if next_run <= now:
        next_run = next_run + timedelta(days=1)
    return int((next_run - now).total_seconds()), next_run


def run_daily(hour=11, minute=30):
    print(f"Daily train_tenders scheduler started for {hour:02d}:{minute:02d}")
    while True:
        wait_seconds, next_run = _seconds_until(hour, minute)
        print(f"Next run at {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
        time.sleep(max(wait_seconds, 1))

        try:
            build_tenders_pkl()
        except Exception as exc:
            print(f"Scheduled run failed: {exc}")


def main():
    parser = argparse.ArgumentParser(description="Pack all tenders into PKL for training")
    parser.add_argument(
        "--daily",
        action="store_true",
        help="Run internal daily scheduler mode (11:30 by default)",
    )
    parser.add_argument("--hour", type=int, default=11, help="Daily scheduler hour (24h)")
    parser.add_argument("--minute", type=int, default=30, help="Daily scheduler minute")
    parser.add_argument(
        "--output",
        default=LATEST_OUTPUT,
        help="Output path for latest PKL file",
    )

    args = parser.parse_args()

    if args.daily:
        run_daily(hour=args.hour, minute=args.minute)
        return

    build_tenders_pkl(output_path=args.output)


if __name__ == "__main__":
    main()
