import pymysql
import random
import datetime
from collections import defaultdict


# 随机时间生成（近7天）
def random_datetime_range():
    now = datetime.datetime.now()
    delta = datetime.timedelta(days=random.randint(0, 6), hours=random.randint(0, 23), minutes=random.randint(0, 59))
    created_at = now - delta
    updated_at = created_at + datetime.timedelta(minutes=random.randint(1, 60))
    return created_at.strftime('%Y-%m-%d %H:%M:%S'), updated_at.strftime('%Y-%m-%d %H:%M:%S')


# 直辖市列表，不处理“市”字
direct_cities = ['北京', '天津', '上海', '重庆']

# 连接数据库
conn = pymysql.connect(
    host='localhost',
    user='root',
    password='123456',
    database='botnet',
    charset='utf8mb4',
    autocommit=True
)
cursor = conn.cursor()

try:
    # === 1. 创建数据库表（如果不存在） ===
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS china_botnet_moobot (
            id INT PRIMARY KEY,
            province VARCHAR(50),
            municipality VARCHAR(50),
            infected_num INT,
            created_at DATETIME,
            updated_at DATETIME
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS global_botnet_moobot (
            id INT PRIMARY KEY,
            country VARCHAR(50),
            infected_num INT,
            created_at DATETIME,
            updated_at DATETIME
        );
    """)

    # === 2. 初始化计数器 ===
    china_counter = defaultdict(int)
    global_counter = defaultdict(int)

    # === 3. 读取 botnet_nodes_moobot 数据 ===
    cursor.execute("SELECT province, city, country FROM botnet_nodes_moobot")
    rows = cursor.fetchall()

    for province, city, country in rows:
        # 预处理省市字段
        if province and province.endswith('省'):
            province = province[:-1]
        if city:
            if city.endswith('市') and city not in direct_cities:
                city = city[:-1]

        global_counter[country] += 1
        if country == '中国':
            china_counter[(province, city)] += 1

    # === 4. 清空 china_botnet_moobot 并重写 ===
    cursor.execute("DELETE FROM china_botnet_moobot")
    for i, ((province, municipality), count) in enumerate(china_counter.items(), start=1):
        created_at, updated_at = random_datetime_range()
        cursor.execute(
            "INSERT INTO china_botnet_moobot (id, province, municipality, infected_num, created_at, updated_at) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (i, province, municipality, count, created_at, updated_at)
        )

    # === 5. 清空 global_botnet_moobot 并重写 ===
    cursor.execute("DELETE FROM global_botnet_moobot")
    for i, (country, count) in enumerate(global_counter.items(), start=1):
        created_at, updated_at = random_datetime_range()
        cursor.execute(
            "INSERT INTO global_botnet_moobot (id, country, infected_num, created_at, updated_at) "
            "VALUES (%s, %s, %s, %s, %s)",
            (i, country, count, created_at, updated_at)
        )

    print("✅ 数据统计与更新完成")

except Exception as e:
    print(f"❌ 发生错误: {e}")

finally:
    cursor.close()
    conn.close()
