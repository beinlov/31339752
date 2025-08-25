from flask import Flask, jsonify
import subprocess
import os
import json
import pymysql
from pymysql import Error
from datetime import datetime

app = Flask(__name__)


@app.route('/start-clean-server', methods=['GET'])
def start_clean_server():
    command = [
        'python', 'httpd.py',
        '--workmode=clean',
        '--cleanglobal',
        '--c2verifymarkclean',
        '--logdir=./logdir'
    ]
    os.makedirs('./logdir', exist_ok=True)

    try:
        subprocess.Popen(command, creationflags=subprocess.CREATE_NEW_CONSOLE)
        return jsonify({'status': 'success', 'message': 'Clean server started.'}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/process-clean1-ips', methods=['GET'])
def process_clean1_ips():
    try:
        log_dir = "./logdir"
        # today_str = datetime.now().strftime('%Y-%m-%d')
        today_str = '2025-06-04'
        log_file = os.path.join(log_dir, f"{today_str}.txt")

        logs = read_and_parse_log(log_file)
        if not logs:
            return jsonify({'status': 'no_log', 'message': '日志文件不存在或为空'})

        # 这里不用再调用 find_clean1_ips，update_ip_status 会自行处理 clean1
        update_result = update_ip_status(logs)

        return jsonify({
            'status': 'success',
            'inserted': list(update_result['inserted']),
            'skipped_existing': list(update_result['skipped_existing']),
            'total_found': len(update_result['inserted']) + len(update_result['skipped_existing'])
        })
    except Exception as e:
        print(f"[ERROR] /process-clean1-ips failed: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/get-clean-records', methods=['GET'])
def get_clean_records():
    db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': '123456',
        'database': 'botnet',
        'charset': 'utf8mb4',
        'cursorclass': pymysql.cursors.DictCursor
    }

    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor() as cursor:
            sql = "SELECT ip, clean_time, operate FROM ip_clean ORDER BY clean_time DESC"
            cursor.execute(sql)
            records = cursor.fetchall()
        connection.close()

        # 转换时间格式
        for r in records:
            if isinstance(r['clean_time'], datetime):
                r['clean_time'] = r['clean_time'].strftime('%Y年%m月%d日 %H:%M:%S')

        return jsonify({
            'status': 'success',
            'count': len(records),
            'records': records
        })
    except Exception as e:
        print(f"[数据库查询错误] {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
def read_and_parse_log(file_path):
    logs = []
    try:
        with open(file_path, 'r') as f:
            for line in f:
                parts = line.strip().split(',')
                if len(parts) < 3:
                    continue
                logs.append({
                    'timestamp': parts[0],
                    'ip': parts[1],
                    'action': parts[2],
                    'details': parts[3:] if len(parts) > 3 else []
                })
    except FileNotFoundError:
        print(f"[错误] 日志文件 {file_path} 不存在")
    return logs


def find_clean1_ips(logs):
    ips = set()
    for log in logs:
        if log['action'].lower() == 'clean1':
            ips.add(log['ip'])
    return ips


def update_ip_status(logs):
    db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': '123456',
        'database': 'botnet',
        'charset': 'utf8mb4',
        'cursorclass': pymysql.cursors.DictCursor
    }

    updated = []
    skipped = []
    connection = None
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor() as cursor:
            for log in logs:
                if log['action'].lower() != 'clean1':
                    continue

                ip = log['ip']
                timestamp = log['timestamp']
                operate = "清除as成功"

                # 插入一条记录（如果重复可忽略）
                try:
                    sql = """
                        INSERT INTO ip_clean (ip, clean_time, operate)
                        VALUES (%s, %s, %s)
                    """
                    cursor.execute(sql, (ip, timestamp, operate))
                    updated.append(ip)
                except pymysql.err.IntegrityError:
                    skipped.append(ip)  # 主键重复（已存在）

        connection.commit()
    except Error as e:
        print(f"[数据库错误] {e}")
        if connection:
            connection.rollback()
    finally:
        if connection:
            connection.close()

    return {'inserted': updated, 'skipped_existing': skipped}


if __name__ == '__main__':
    app.run(port=5000, debug=True)
