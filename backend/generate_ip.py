import asyncio
import random
import pymysql
import pandas as pd
from datetime import datetime, timedelta
from ip_location.ip_query import ip_query
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 数据库配置
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "root",
    "database": "botnet"
}


async def ensure_table_exists(cursor, botnet_type):
    """确保数据表存在"""
    table_name = f"botnet_nodes_{botnet_type}"
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id INT AUTO_INCREMENT PRIMARY KEY,
            ip VARCHAR(15) NOT NULL,
            longitude FLOAT,
            latitude FLOAT,
            country VARCHAR(50),
            province VARCHAR(50),
            city VARCHAR(50),
            continent VARCHAR(50),
            isp VARCHAR(255),
            asn VARCHAR(50),
            status ENUM('active', 'inactive') DEFAULT 'active',
            last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            is_china BOOLEAN DEFAULT FALSE,
            INDEX idx_ip (ip),
            INDEX idx_location (country, province, city),
            INDEX idx_status (status),
            INDEX idx_last_active (last_active),
            INDEX idx_is_china (is_china)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)


async def insert_ip_data(cursor, botnet_type, ip_info, ip):
    """插入IP数据到对应的表"""
    try:
        if not ip_info:
            return False

        country = ip_info.get('country', '')
        province = ip_info.get('province', '')
        city = ip_info.get('city', '')
        longitude = float(ip_info.get('longitude', 0))
        latitude = float(ip_info.get('latitude', 0))

        status = 'active' if random.random() > 0.2 else 'inactive'
        last_active = datetime.now() - timedelta(hours=random.randint(0, 48))

        table_name = f"botnet_nodes_{botnet_type}"
        cursor.execute(f"""
            INSERT INTO {table_name} 
            (ip, longitude, latitude, country, province, city, continent, isp, asn, status, last_active, is_china)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            ip, longitude, latitude, country, province, city,
            ip_info.get('continent', ''), ip_info.get('isp', ''), ip_info.get('asn', ''),
            status, last_active,
            country == '中国'
        ))
        return True

    except Exception as e:
        logger.error(f"Error inserting IP data: {e}")
        return False


async def generate_botnet_data(botnet_type, ip_list):
    """为指定的僵尸网络类型处理 IP 数据"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()

        await ensure_table_exists(cursor, botnet_type)

        success_count = 0
        china_count = 0
        global_count = 0

        for idx, ip in enumerate(ip_list):
            ip_info = await ip_query(ip)
            if await insert_ip_data(cursor, botnet_type, ip_info, ip):
                success_count += 1
                if ip_info and ip_info.get('country', '') == '中国':
                    china_count += 1
                else:
                    global_count += 1

            if (idx + 1) % 100 == 0:
                conn.commit()
                logger.info(f"{botnet_type} progress: {success_count}/{len(ip_list)} "
                            f"(China: {china_count}, Global: {global_count})")

        conn.commit()
        logger.info(f"Completed generating data for {botnet_type}")
        logger.info(f"Total nodes: {success_count} (China: {china_count}, Global: {global_count})")

    except Exception as e:
        logger.error(f"Error generating data for {botnet_type}: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()


async def main():
    """主函数"""
    xlsx_path = '../ramnit.xlsx'  # 修改为你的 .xlsx 文件路径
    botnet_type = 'ramnit'

    try:
        # 读取 Excel 文件
        df = pd.read_excel(xlsx_path)  # 不需要 encoding

        if 'IP地址' not in df.columns:
            logger.error("Excel 文件中缺少 'IP地址' 列")
            return

        ip_list = df['IP地址'].dropna().unique().tolist()
        logger.info(f"Loaded {len(ip_list)} IPs from Excel")

        await generate_botnet_data(botnet_type, ip_list)

    except Exception as e:
        logger.error(f"Error in main(): {e}")


if __name__ == "__main__":
    asyncio.run(main())
