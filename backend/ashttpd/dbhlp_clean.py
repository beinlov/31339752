import sys
import pymysql
from address_parse import get_address


# 定义 add 函数，接收一个包含多个数据项（如IP地址和时间戳）的列表 'items'
def add(items):
    print("    db connecting...")  # 提示正在连接数据库

    # 创建与 MySQL 数据库的连接
    conn = pymysql.connect(
        host='127.0.0.1',  # 数据库的主机地址
        port=36906,  # 数据库端口
        user='root',  # 用户名
        password='root@root1123',  # 密码
        database='bdp-eagle'  # 连接的数据库
    )

    # 获取数据库操作游标，用于执行 SQL 查询
    cursor = conn.cursor()

    print("    db adding.")  # 提示正在添加数据到数据库
    i = 0  # 初始化计数器，用于跟踪已处理的项数

    # 遍历每一项（每一项包含 IP 地址和时间戳）
    for item in items:
        # 提取数据项中的 IP 地址和时间戳
        ip = item['ip']
        ts = item['ts']

        # 获取 IP 地址对应的国家和省区信息
        nation, province = get_address(ip)

        # 如果国家和省区都为 '中国'，则中止循环
        if nation == '中国' and province == '中国':
            break

        # 如果是中国的IP地址
        if nation == '中国':
            area_type = 0  # 设置 area_type 为 0，表示中国
            where_from = '广东'  # 来源设置为广东（假定所有中国IP均来自广东）
            where_clean = province  # 清理区域设置为省区名称

        # 如果是非中国的IP地址且没有错误的国家信息（即 'nan'）
        elif nation != 'nan':
            area_type = 1  # 设置 area_type 为 1，表示国外
            where_from = '中国'  # 来源设置为中国
            where_clean = nation  # 清理区域设置为国家名称
            province = nation  # 如果是国外的，省和国家设置一样（通常没有单独的省级信息）
        else:
            continue  # 如果没有有效的国家信息，跳过当前项

        # 构建 INSERT 查询语句，将数据插入 `events_clean_trends` 表
        insert_query = "INSERT IGNORE `events_clean_trends` SET `where_from` = %s, `where_clean` = %s, `update_time` = %s, `company_type` = 'A', `area_type` = %s, `ip` = %s"
        cursor.execute(insert_query, (where_from, where_clean, ts, area_type, ip))  # 执行查询

        # 查询总表（`as_main`）是否已包含该 IP 地址
        cursor = conn.cursor()  # 获取新的游标

        # 构建 SELECT 查询语句，检查 `as_main` 表中是否已存在该 IP
        select_query = "SELECT COUNT(*) FROM as_main WHERE ip = %s"
        cursor.execute(select_query, ip)  # 执行查询

        # 获取查询结果
        result = cursor.fetchone()

        # 判断查询结果是否存在该 IP 地址的记录
        existflag = False
        if result[0] > 0:  # 如果查询结果大于 0，说明存在该记录
            existflag = True  # 设置 existflag 为 True，表示记录已存在
            # 执行更新操作，设置该 IP 地址的 `判断符` 字段为 1
            update_query = "UPDATE as_main SET 判断符 = 1 WHERE ip = %s"
            cursor.execute(update_query, ip)
        else:
            # 如果记录不存在，则插入新的记录到 `as_main` 表
            insert_query = f"INSERT IGNORE INTO as_main (IP, 省区, 判断符, 是否判断) VALUES (%s, %s, %s, %s)"
            cursor.execute(insert_query, (ip, province, 1, 0))  # 插入新记录

        i += 1  # 处理项计数器加 1

        # 打印当前处理进度：已处理项数 / 总项数，显示当前 IP 地址及其国家、省区，以及该 IP 是否存在于主表中
        sys.stdout.write(
            "\r%d/%d   %s %s %s  IP是否在主表格%s    " % (i, len(items), ip, nation, province, str(existflag)))

        print("    db committing...")  # 提示正在提交事务

        # 提交当前事务到数据库
        conn.commit()

    # 打印结束提示信息
    print("")
    print("    db closing...")  # 提示数据库连接即将关闭

    # 关闭游标和数据库连接
    cursor.close()
    conn.close()

    print("db ok...")  # 数据库操作完成提示

# 这个代码的主要功能是将 IP 地址及其地理位置信息存储到 MySQL 数据库中，并更新相关表的状态。其核心逻辑包括：
# 解析 IP 地址的地理位置。
# 将数据插入到 events_clean_trends 表中。
# 检查并更新 as_main 表中的记录。
# 在控制台输出处理进度。