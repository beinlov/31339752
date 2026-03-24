import pymysql
import pandas as pd
from datetime import datetime
from config import DB_CONFIG
import sys
import os

TABLE = "botnet_nodes_utg_q_008"

def get_table_info():
    conn = pymysql.connect(**DB_CONFIG)
    cur = conn.cursor()
    try:
        cur.execute(f"DESCRIBE {TABLE}")
        cols = cur.fetchall()
        print("="*80)
        print(f"Table: {TABLE}")
        print("="*80)
        info = {}
        for c in cols:
            print(f"{c[0]:<20} {c[1]:<25} {c[2]:<10}")
            info[c[0]] = {'type': c[1], 'null': c[2]}
        print("="*80)
        return info
    finally:
        cur.close()
        conn.close()

def read_excel_file(path):
    print(f"\nReading: {path}")
    try:
        df = pd.read_excel(path)
        print(f"Rows: {len(df)}")
        print(f"\nColumns:")
        for i, col in enumerate(df.columns, 1):
            print(f"  {i}. {col}")
        print("\nPreview:")
        print(df.head(3))
        return df
    except Exception as e:
        print(f"Error: {e}")
        return None

def map_row(row, col_info):
    data = {}
    for field in col_info.keys():
        if field == 'id':
            continue
        
        if field == 'ip':
            val = row.get('IP', row.get('ip'))
        elif field == 'country':
            val = row.get('country')
            if pd.isna(val):
                for k in row.keys():
                    if 'country' in str(k).lower() or 'guo' in str(k).lower():
                        val = row.get(k)
                        break
        elif field == 'province':
            val = row.get('province')
            if pd.isna(val):
                for k in row.keys():
                    if 'province' in str(k).lower() or 'sheng' in str(k).lower():
                        val = row.get(k)
                        break
        elif field == 'city':
            val = row.get('city', '')
            if pd.isna(val):
                for k in row.keys():
                    if 'shi' in str(k).lower() or 'city' in str(k).lower():
                        val = row.get(k, '')
                        break
            if val == '*' or pd.isna(val):
                val = None
            elif isinstance(val, str):
                val = val.strip() or None
        elif field == 'area':
            val = row.get('city1', '')
            if pd.isna(val):
                for k in row.keys():
                    if 'qu' in str(k).lower() or 'xian' in str(k).lower() or 'city1' in str(k).lower():
                        val = row.get(k, '')
                        break
            if val == '*' or pd.isna(val):
                val = None
            elif isinstance(val, str):
                val = val.strip() or None
        elif field == 'unit':
            val = row.get('unit')
            if pd.isna(val):
                for k in row.keys():
                    if 'unit' in str(k).lower() or 'danwei' in str(k).lower():
                        val = row.get(k)
                        break
        elif field == 'industry':
            val = row.get('industry')
            if pd.isna(val):
                for k in row.keys():
                    if 'industry' in str(k).lower() or 'hangye' in str(k).lower():
                        val = row.get(k)
                        break
        elif field == 'communication_time':
            val = row.get('communication_time')
            if pd.isna(val):
                for k in row.keys():
                    if 'time' in str(k).lower() or 'tongxin' in str(k).lower():
                        val = row.get(k)
                        break
            if pd.isna(val) or val == '*':
                val = datetime.now()
        elif field == 'status':
            val = row.get('status', 'active')
        else:
            val = row.get(field)
        
        if val == '*' or pd.isna(val):
            val = None
        if isinstance(val, str):
            val = val.strip()
            if val == '' or val == '*':
                val = None
        
        data[field] = val
    
    return data

def insert_data(df, col_info):
    conn = pymysql.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    try:
        ok = 0
        err = 0
        
        print(f"\nImporting to {TABLE}...")
        
        for idx, row in df.iterrows():
            try:
                data = map_row(row, col_info)
                fields = [f for f in data.keys() if f != 'id']
                sql = f"INSERT INTO {TABLE} ({','.join(fields)}) VALUES ({','.join(['%s']*len(fields))})"
                cur.execute(sql, [data[f] for f in fields])
                ok += 1
                
                if (idx + 1) % 100 == 0:
                    print(f"Processed: {idx + 1}/{len(df)}")
                    conn.commit()
                
            except Exception as e:
                err += 1
                if err <= 5:
                    print(f"Row {idx + 1} error: {e}")
        
        conn.commit()
        print(f"\nSuccess: {ok}, Failed: {err}, Total: {len(df)}")
        
    finally:
        cur.close()
        conn.close()

def main():
    print("="*80)
    print("Database Import Tool")
    print("="*80)
    
    print("\nEnter Excel file path:")
    path = input("Path: ").strip().strip('"')
    
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return
    
    col_info = get_table_info()
    df = read_excel_file(path)
    
    if df is None:
        return
    
    ans = input(f"\nImport {len(df)} rows? (yes/no): ")
    if ans.lower() in ['yes', 'y']:
        insert_data(df, col_info)
        print("Done!")
    else:
        print("Cancelled")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nCancelled")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
