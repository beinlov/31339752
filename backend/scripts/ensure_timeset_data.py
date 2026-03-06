from __future__ import annotations

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
    # 只确保active和cleaned字段存在
    # 使用统一的字段名：global_active, china_active, global_cleaned, china_cleaned
    if not _column_exists(cursor, timeset_table, "global_active"):
        cursor.execute(
            f"""
            ALTER TABLE {timeset_table}
            ADD COLUMN global_active INT NOT NULL DEFAULT 0 COMMENT '全球活跃节点数量'
            """
        )
    
    if not _column_exists(cursor, timeset_table, "china_active"):
        cursor.execute(
            f"""
            ALTER TABLE {timeset_table}
            ADD COLUMN china_active INT NOT NULL DEFAULT 0 COMMENT '中国活跃节点数量'
            AFTER global_active
            """
        )
    
    if not _column_exists(cursor, timeset_table, "global_cleaned"):
        cursor.execute(
            f"""
            ALTER TABLE {timeset_table}
            ADD COLUMN global_cleaned INT NOT NULL DEFAULT 0 COMMENT '全球已清除节点数量'
            AFTER china_active
            """
        )
    
    if not _column_exists(cursor, timeset_table, "china_cleaned"):
        cursor.execute(
            f"""
            ALTER TABLE {timeset_table}
            ADD COLUMN china_cleaned INT NOT NULL DEFAULT 0 COMMENT '中国已清除节点数量'
            AFTER global_cleaned
            """
        )


def _get_counts(cursor, botnet_type: str) -> tuple[int, int, int, int, int, int] | None:
    """
    返回: (global_count, china_count, global_active, china_active, global_cleaned, china_cleaned)
    """
    node_table = f"botnet_nodes_{botnet_type}"
    if not _table_exists(cursor, node_table):
        return None

    # 统计全球总数和active/cleaned数量
    cursor.execute(f"""
        SELECT 
            COUNT(*) as total_count,
            SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active_count,
            SUM(CASE WHEN status = 'cleaned' THEN 1 ELSE 0 END) as cleaned_count
        FROM {node_table}
    """)
    row = cursor.fetchone()
    global_count = int(row["total_count"] or 0)
    global_active = int(row["active_count"] or 0)
    global_cleaned = int(row["cleaned_count"] or 0)

    # 统计中国总数和active/cleaned数据
    china_count = 0
    china_active = 0
    china_cleaned = 0
    global_table = f"global_botnet_{botnet_type}"
    if _table_exists(cursor, global_table):
        cursor.execute(
            f"""
            SELECT 
                SUM(infected_num) as total_china,
                SUM(active_num) as active_total,
                SUM(cleaned_num) as cleaned_total
            FROM {global_table} 
            WHERE country = '中国'
            """
        )
        row = cursor.fetchone()
        if row:
            china_count = int(row["total_china"] or 0)
            china_active = int(row["active_total"] or 0)
            china_cleaned = int(row["cleaned_total"] or 0)

    return global_count, china_count, global_active, china_active, global_cleaned, china_cleaned


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
                node_table = f"botnet_nodes_{botnet_type}"
                
                if not _table_exists(cursor, timeset_table):
                    _log(f"[{botnet_type}] skip: timeset table not found ({timeset_table})")
                    continue

                _ensure_timeset_schema(cursor, timeset_table)

                # 检查 nodes 表是否存在
                if not _table_exists(cursor, node_table):
                    _log(f"[{botnet_type}] skip: nodes table not found ({node_table})")
                    continue

                existing = _get_existing_dates(cursor, timeset_table, range_start, today)
                missing = [
                    range_start + timedelta(days=i)
                    for i in range((today - range_start).days + 1)
                    if (range_start + timedelta(days=i)) not in existing
                ]

                if not missing:
                    _log(f"[{botnet_type}] ok: no missing dates in last 30 days")
                    continue

                _log(f"[{botnet_type}] missing {len(missing)} day(s): {missing[0]} ~ {missing[-1]}")

                # 对每一天，从 botnet_nodes 表按 updated_at 日期统计
                filled_count = 0
                for d in missing:
                    cursor.execute(
                        f"""
                        SELECT 
                            COUNT(DISTINCT ip) as total_ips,
                            COUNT(DISTINCT CASE WHEN status = 'active' THEN ip END) as active_ips,
                            COUNT(DISTINCT CASE WHEN status = 'cleaned' THEN ip END) as cleaned_ips,
                            COUNT(DISTINCT CASE WHEN country = '中国' THEN ip END) as china_total,
                            COUNT(DISTINCT CASE WHEN country = '中国' AND status = 'active' THEN ip END) as china_active,
                            COUNT(DISTINCT CASE WHEN country = '中国' AND status = 'cleaned' THEN ip END) as china_cleaned
                        FROM {node_table}
                        WHERE DATE(updated_at) = %s
                        """,
                        (d,)
                    )
                    result = cursor.fetchone()
                    
                    global_count = int(result['total_ips'] or 0)
                    global_active = int(result['active_ips'] or 0)
                    global_cleaned = int(result['cleaned_ips'] or 0)
                    china_count = int(result['china_total'] or 0)
                    china_active = int(result['china_active'] or 0)
                    china_cleaned = int(result['china_cleaned'] or 0)
                    
                    # 即使当天没有 updated_at 的记录，也写入0值以保证30天数据完整
                    # 使用 INSERT IGNORE 确保不会修改已存在的日期条目
                    cursor.execute(
                        f"""
                        INSERT IGNORE INTO {timeset_table} (date, global_count, china_count, global_active, china_active, global_cleaned, china_cleaned)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """,
                        (d, global_count, china_count, global_active, china_active, global_cleaned, china_cleaned),
                    )
                    if cursor.rowcount > 0:
                        filled_count += 1

                _log(f"[{botnet_type}] filled {filled_count}/{len(missing)} day(s) into {timeset_table} (based on nodes.updated_at)")

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
