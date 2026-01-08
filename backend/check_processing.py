"""检查数据处理进度"""
import pymysql
from config import DB_CONFIG

conn = pymysql.connect(**DB_CONFIG)
cursor = conn.cursor()

print("=" * 60)
print("检查各僵尸网络类型的数据")
print("=" * 60)

for botnet_type in ['test', 'ramnit']:
    try:
        # 检查节点表
        cursor.execute(f"SELECT COUNT(*) FROM botnet_nodes_{botnet_type}")
        node_count = cursor.fetchone()[0]
        
        # 检查通信表
        cursor.execute(f"SELECT COUNT(*) FROM botnet_communications_{botnet_type}")
        comm_count = cursor.fetchone()[0]
        
        # 检查最新数据 - test表用created_at，其他用created_time
        time_field = 'created_at' if botnet_type == 'test' else 'created_time'
        cursor.execute(f"SELECT MAX({time_field}) FROM botnet_nodes_{botnet_type}")
        latest_time = cursor.fetchone()[0]
        
        print(f"\n{botnet_type.upper()}:")
        print(f"  节点数: {node_count}")
        print(f"  通信记录数: {comm_count}")
        print(f"  最新数据时间: {latest_time}")
        
    except Exception as e:
        print(f"\n{botnet_type.upper()}: 表不存在或错误 - {e}")

cursor.close()
conn.close()

print("\n" + "=" * 60)
print("如果test的数据没有增加，说明C2服务器还在返回ramnit数据")
print("=" * 60)
