import os
import sys
import time
from datetime import date, timedelta
from datetime import datetime

import pymysql
from pymysql.cursors import DictCursor

_BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

from config import ALLOWED_BOTNET_TYPES, DB_CONFIG


def _log(msg: str) -> None:
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)


def _table_exists(cursor, table_name: str) -> bool:
    cursor.execute(
        """
        SELECT COUNT(*) as count
        FROM information_schema.tables
        WHERE table_schema = DATABASE()
          AND table_name = %s
        """,
        (table_name,),
    )
    return cursor.fetchone()["count"] > 0


def _column_exists(cursor, table_name: str, column_name: str) -> bool:
    cursor.execute(
        """
        SELECT COUNT(*) as count
        FROM information_schema.columns
        WHERE table_schema = DATABASE()
          AND table_name = %s
          AND column_name = %s
        """,
        (table_name, column_name),
    )
    row = cursor.fetchone()
    if isinstance(row, dict):
        return row["count"] > 0
    return row[0] > 0


def _ensure_timeset_schema(cursor, timeset_table: str) -> None:
    has_global_count = _column_exists(cursor, timeset_table, "global_count")
    if not has_global_count:
        has_count = _column_exists(cursor, timeset_table, "count")
        if has_count:
            cursor.execute(
                f"""
                ALTER TABLE {timeset_table}
                CHANGE COLUMN count global_count INT NOT NULL DEFAULT 0 COMMENT '全球节点数量'
                """
            )
        else:
            cursor.execute(
                f"""
                ALTER TABLE {timeset_table}
                ADD COLUMN global_count INT NOT NULL DEFAULT 0 COMMENT '全球节点数量'
                """
            )

    has_china_count = _column_exists(cursor, timeset_table, "china_count")
    if not has_china_count:
        cursor.execute(
            f"""
            ALTER TABLE {timeset_table}
            ADD COLUMN china_count INT NOT NULL DEFAULT 0 COMMENT '中国节点数量'
            AFTER global_count
            """
        )


def _get_counts(cursor, botnet_type: str) -> tuple[int, int] | None:
    node_table = f"botnet_nodes_{botnet_type}"
    if not _table_exists(cursor, node_table):
        return None

    cursor.execute(f"SELECT COUNT(*) as total FROM {node_table}")
    global_count = int(cursor.fetchone()["total"])

    china_count = 0
    global_table = f"global_botnet_{botnet_type}"
    if _table_exists(cursor, global_table):
        cursor.execute(
            f"SELECT infected_num FROM {global_table} WHERE country = '中国' LIMIT 1"
        )
        row = cursor.fetchone()
        if row and row.get("infected_num") is not None:
            try:
                china_count = int(row["infected_num"])
            except Exception:
                china_count = 0

    return global_count, china_count


def _get_last_timeset_date(cursor, timeset_table: str) -> date | None:
    cursor.execute(f"SELECT MAX(date) as max_date FROM {timeset_table}")
    row = cursor.fetchone()
    if not row or row.get("max_date") is None:
        return None
    return row["max_date"]


def _get_existing_dates(cursor, timeset_table: str, start_date: date, end_date: date) -> set[date]:
    cursor.execute(
        f"""
        SELECT date
        FROM {timeset_table}
        WHERE date >= %s AND date <= %s
        """,
        (start_date, end_date),
    )
    return {r["date"] for r in cursor.fetchall()}


def ensure_recent_30_days_data() -> None:
    today = date.today()
    range_start = today - timedelta(days=29)

    _log(f"Start ensure timeset data. Window: {range_start} ~ {today}")

    conn = pymysql.connect(**DB_CONFIG)
    try:
        cursor = conn.cursor(DictCursor)
        try:
            for botnet_type in ALLOWED_BOTNET_TYPES:
                timeset_table = f"botnet_timeset_{botnet_type}"
                if not _table_exists(cursor, timeset_table):
                    _log(f"[{botnet_type}] skip: timeset table not found ({timeset_table})")
                    continue

                _ensure_timeset_schema(cursor, timeset_table)

                counts = _get_counts(cursor, botnet_type)
                if not counts:
                    _log(f"[{botnet_type}] skip: nodes table not found or unreadable")
                    continue

                global_count, china_count = counts

                existing = _get_existing_dates(cursor, timeset_table, range_start, today)
                missing = [
                    range_start + timedelta(days=i)
                    for i in range((today - range_start).days + 1)
                    if (range_start + timedelta(days=i)) not in existing
                ]

                if not missing:
                    _log(f"[{botnet_type}] ok: no missing dates in last 30 days")
                    continue

                _log(
                    f"[{botnet_type}] missing {len(missing)} day(s): {missing[0]} ~ {missing[-1]} | "
                    f"write global_count={global_count}, china_count={china_count}"
                )

                for d in missing:
                    cursor.execute(
                        f"""
                        INSERT INTO {timeset_table} (date, global_count, china_count)
                        VALUES (%s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                            global_count = VALUES(global_count),
                            china_count = VALUES(china_count)
                        """,
                        (d, global_count, china_count),
                    )

                _log(f"[{botnet_type}] filled {len(missing)} day(s) into {timeset_table}")

        finally:
            cursor.close()
    finally:
        conn.close()

    _log("Ensure timeset data round complete")


def _wait_for_mysql(max_wait_seconds: int = 180) -> bool:
    deadline = time.time() + max_wait_seconds
    last_error = None
    _log(f"Waiting for MySQL (max {max_wait_seconds}s)...")
    while time.time() < deadline:
        try:
            conn = pymysql.connect(**DB_CONFIG)
            try:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                _log("MySQL is ready")
                return True
            finally:
                conn.close()
        except Exception as e:
            last_error = e
            _log(f"MySQL not ready yet: {e}. Retrying in 3s...")
            time.sleep(3)
    if last_error:
        _log(f"MySQL not ready: {last_error}")
    return False


def main() -> None:
    _log("Botnet Timeset Data Ensurer started")
    if not _wait_for_mysql():
        return

    while True:
        try:
            ensure_recent_30_days_data()
        except Exception as e:
            _log(f"ensure_timeset_data error: {e}")

        next_run = datetime.now() + timedelta(hours=3)
        _log(f"Next check at {next_run.strftime('%Y-%m-%d %H:%M:%S')} (sleep 3h)")
        time.sleep(3 * 60 * 60)


if __name__ == "__main__":
    main()
