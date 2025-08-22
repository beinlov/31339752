import sys
import pymysql
from address_parse import get_address

# MySQL数据库连接信息
host = '127.0.0.1'  # 数据库主机地址
db_port = 36906      # 数据库端口
database = 'bdp-eagle'  # 数据库名称
user = 'root'        # 数据库用户名
password = 'root@root1123'  # 数据库密码


# 函数add2：向数据库表中插入数据
def add2(items):
    # 创建数据库连接
    print("    db connecting...")  # 输出数据库连接提示
    connection = pymysql.connect(host=host, port=db_port, database=database, user=user, password=password)
    print("    db connected.")  # 输出数据库连接成功提示
    cursor = connection.cursor()  # 获取游标对象，用于执行 SQL 查询
    print("    db adding.")  # 输出正在添加数据提示
    i = 0
    # 构建插入语句的起始部分
    insert_words = ''  # 用于存储每条插入数据的语句部分
    insert_query = 'INSERT IGNORE INTO as_main (IP, 访问时间, 国家, 省区) VALUES '  # 构造插入语句

    # 遍历items列表，将每一项插入到数据库
    for item in items:
        ip = item['ip']  # 提取IP地址
        ts = item['ts']  # 提取时间戳
        nation, province = get_address(ip)  # 获取IP对应的国家和省区
        if nation != '中国':
            province = nation  # 如果是国外的，省和国家设置一样
        # 构建每条记录的插入部分
        insert_words += '("{ip}","{ts}","{nation}","{province}"),'

    # 拼接完整的插入查询语句
    inserts_query = (insert_query + insert_words).rstrip(',')  # 去掉最后的逗号
    print(inserts_query)  # 打印完整的插入查询语句

    # 执行插入操作
    cursor.execute(inserts_query)

    print("")
    print("    db committing...")  # 输出数据库提交提示
    # 提交事务并关闭连接
    connection.commit()
    print("    db closing...")  # 输出关闭数据库连接提示
    cursor.close()  # 关闭游标
    connection.close()  # 关闭数据库连接
    print("db ok...")  # 输出操作成功提示


# 函数add3：向另一个数据库表插入数据，处理的字段和表不同
def add3(items):
    # 创建数据库连接
    print("    db connecting...")  # 输出数据库连接提示
    connection = pymysql.connect(host=host, port=db_port, database=database, user=user, password=password)
    print("    db connected.")  # 输出数据库连接成功提示
    cursor = connection.cursor()  # 获取游标对象，用于执行 SQL 查询
    print("    db adding.")  # 输出正在添加数据提示
    i = 0
    insert_words = ''  # 用于存储每条插入数据的语句部分
    insert_query = 'INSERT IGNORE INTO as_nodes (IP, daily, accesstime, nation, province, UUID) VALUES '  # 构造插入语句

    # 遍历items列表，将每一项插入到数据库
    for item in items:
        ip = item['ip']  # 提取IP地址
        ts = item['ts']  # 提取时间戳
        daily = ts[:10]  # 提取日期部分（取前10个字符，即日期部分）
        uuid = item.get('uuid', "")  # 获取UUID，如果没有则默认空字符串
        nation, province = get_address(ip)  # 获取IP对应的国家和省区
        if nation != '中国':
            province = nation  # 如果是国外的，省和国家设置一样

        # 构建每条记录的插入部分
        insert_words += f'("{ip}","{daily}","{ts}","{nation}","{province}","{uuid}"),'

    # 拼接完整的插入查询语句
    inserts_query = (insert_query + insert_words).rstrip(',')  # 去掉最后的逗号
    print(inserts_query)  # 打印完整的插入查询语句

    # 执行插入操作
    cursor.execute(inserts_query)

    print("")
    print("    db committing...")  # 输出数据库提交提示
    # 提交事务并关闭连接
    connection.commit()
    print("    db closing...")  # 输出关闭数据库连接提示
    cursor.close()  # 关闭游标
    connection.close()  # 关闭数据库连接
    print("db ok...")  # 输出操作成功提示


# 函数add：批量插入数据到数据库，分批次进行
def add(items):
    while len(items) > 0:
        bat = items[:500]  # 从 items 中提取前500个元素作为一批数据
        items = items[500:]  # 将 items 列表中前500个元素移除
        if bat:
            add2(bat)  # 调用 add2 函数将当前批次的数据插入到数据库


# 函数add_uuid：批量插入数据到数据库，分批次进行，并处理UUID字段
def add_uuid(items):
    while len(items) > 0:
        bat = items[:500]  # 从 items 中提取前500个元素作为一批数据
        items = items[500:]  # 将 items 列表中前500个元素移除
        if bat:
            add3(bat)  # 调用 add3 函数将当前批次的数据插入到数据库

# 这个代码的主要功能是将 IP 地址及其相关信息批量插入到 MySQL 数据库的两个表中：as_main 和 as_nodes。其核心逻辑包括：
# 解析 IP 地址的地理位置。
# 构建批量插入的 SQL 语句。
# 分批次处理数据，每次最多处理 500 条记录。