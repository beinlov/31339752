import pymysql
import pandas as pd
from datetime import datetime
from config import DB_CONFIG

EXCEL_FILE = "D:\\dell\\Desktop\\课件文件\\1.威海 研究生资料\\1.僵尸网络资料\\0321归属\\20260321汇总IP归属（114+国口）发哈工大.xlsx"
TABLE_NAME = "botnet_nodes_utg_q_008"

def get_table_structure():
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    try:
        cursor.execute(f"DESCRIBE {TABLE_NAME}")
        columns = cursor.fetchall()
        print("="*80)
        print(f"Table: {TABLE_NAME}")
        print("="*80)
        column_info = {}
        for col in columns:
            print(f"{col[0]:<20} {col[1]:<20} {col[2]:<10}")
            column_info[col[0]] = {'type': col[1], 'null': col[2]}
        print("="*80)
        return column_info
    finally:
        cursor.close()
        conn.close()

def read_excel():
    print(f"\nReading: {EXCEL_FILE}")
    df = pd.read_excel(EXCEL_FILE)
    print(f"Rows: {len(df)}")
    print("\nColumns:", list(df.columns))
    print("\nPreview:")
    print(df.head(3))
    return df

def map_row(row, col_info):
    data = {}
    for field in col_info.keys():
        if field == 'id':
            continue
        if field == 'ip':
            data[field] = row.get('IP', row.get('ip'))
        elif field == 'country':
            data[field] = row.get('国家', row.get('country'))
        elif field == 'province':
            data[field] = row.get('省份', row.get('province'))
        elif field == 'city':
            c1 = row.get('市', row.get('city', ''))
            c2 = row.get('区县', row.get('city1', ''))
            if c1 == '*' or pd.isna(c1): c1 = ''
            if c2 == '*' or pd.isna(c2): c2 = ''
            if c1 and c2:
                data[field] = f"{c1} {c2}"
            else:
                data[field] = c1 or c2 or None
        elif field == 'unit':
            data[field] = row.get('单位', row.get('unit'))
        elif field == 'industry':
            data[field] = row.get('行业', row.get('industry'))
        elif field == 'communication_time':
            val = row.get('通信时间', row.get('communication_time'))
            data[field] = datetime.now() if pd.isna(val) or val == '*' else val
        elif field == 'status':
            data[field] = row.get('状态', row.get('status', 'active'))
        else:
            data[field] = row.get(field)
        if data[field] == '*' or pd.isna(data[field]):
            data[field] = None
        if isinstance(data[field], str):
            data[field] = data[field].strip() or None
    return data

def insert_data(df, col_info):
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    try:
        success = 0
        for idx, row in df.iterrows():
            try:
                data = map_row(row, col_info)
                fields = [f for f in data.keys() if f != 'id']
                sql = f"INSERT INTO {TABLE_NAME} ({','.join(fields)}) VALUES ({','.join(['%s']*len(fields))})"
                cursor.execute(sql, [data[f] for f in fields])
                success += 1
                if (idx+1) % 100 == 0:
                    print(f"Processed {idx+1}/{len(df)}")
                    conn.commit()
            except Exception as e:
                print(f"Row {idx+1} error: {e}")
        conn.commit()
        print(f"\nSuccess: {success}/{len(df)}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    print("Excel Import Script")
    col_info = get_table_structure()
    df = read_excel()
    confirm = input(f"\nImport {len(df)} rows? (yes/no): ")
    if confirm.lower() in ['yes', 'y']:
        insert_data(df, col_info)