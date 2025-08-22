import pymysql

# 连接数据库
conn = pymysql.connect(
    host='localhost',
    user='root',
    password='root',
    database='botnet',
    charset='utf8mb4'
)

# 定义直辖市列表
direct_cities = ['北京', '上海', '天津', '重庆']

try:
    with conn.cursor() as cursor:
        # 更新 province 字段：去掉“省”
        sql_province = """
            UPDATE china_botnet_ramnit
            SET province = REPLACE(province, '省', '')
            WHERE province LIKE '%省';
        """
        cursor.execute(sql_province)

        # 查询所有 municipality 的唯一值
        cursor.execute("SELECT DISTINCT municipality FROM china_botnet_ramnit;")
        municipalities = cursor.fetchall()

        for (city,) in municipalities:
            if city is None:
                continue
            # 如果不是直辖市，且包含“市”，就删除“市”
            if city not in direct_cities and city.endswith('市'):
                new_city = city.replace('市', '')
                sql_update_municipality = """
                    UPDATE china_botnet_ramnit
                    SET municipality = %s
                    WHERE municipality = %s;
                """
                cursor.execute(sql_update_municipality, (new_city, city))

        conn.commit()
        print("更新成功。")

finally:
    conn.close()
