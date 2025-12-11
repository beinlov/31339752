"""
重建聚合表脚本
清空并重新生成所有聚合表，确保数据一致性
"""
import pymysql
import sys
import os
from datetime import datetime

# 添加父目录到路径以便导入config
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import DB_CONFIG

# 僵尸网络类型列表
BOTNET_TYPES = ['asruex', 'mozi', 'andromeda', 'moobot', 'ramnit', 'leethozer']

def rebuild_aggregation_tables(cursor, botnet_type):
    """重建指定僵尸网络的聚合表"""
    
    print(f"\n{'='*60}")
    print(f"重建 {botnet_type} 的聚合表")
    print(f"{'='*60}")
    
    node_table = f"botnet_nodes_{botnet_type}"
    china_table = f"china_botnet_{botnet_type}"
    global_table = f"global_botnet_{botnet_type}"
    
    # 检查原始表是否存在
    cursor.execute("""
        SELECT COUNT(*) as count 
        FROM information_schema.tables 
        WHERE table_schema = %s AND table_name = %s
    """, (DB_CONFIG['database'], node_table))
    
    if cursor.fetchone()['count'] == 0:
        print(f"[!] 原始表 {node_table} 不存在，跳过")
        return
    
    # 1. 清空聚合表
    print("[-] 清空旧的聚合表...")
    try:
        cursor.execute(f"TRUNCATE TABLE {china_table}")
        print(f"   [+] 清空 {china_table}")
    except Exception as e:
        print(f"   [!] {china_table} 可能不存在: {e}")
    
    try:
        cursor.execute(f"TRUNCATE TABLE {global_table}")
        print(f"   [+] 清空 {global_table}")
    except Exception as e:
        print(f"   [!] {global_table} 可能不存在: {e}")
    
    # 2. 确保聚合表存在
    print("\n[+] 创建/确保聚合表结构...")
    
    # 中国聚合表
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {china_table} (
            id INT AUTO_INCREMENT PRIMARY KEY,
            province VARCHAR(100) NOT NULL COMMENT '省份',
            municipality VARCHAR(100) NOT NULL COMMENT '城市',
            infected_num INT NOT NULL DEFAULT 0 COMMENT '感染数量',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
            UNIQUE KEY unique_location (province, municipality),
            INDEX idx_province (province),
            INDEX idx_municipality (municipality),
            INDEX idx_updated (updated_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='中国区域僵尸网络统计表'
    """)
    print(f"   [+] {china_table} 表结构已确认")
    
    # 全球聚合表
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {global_table} (
            id INT AUTO_INCREMENT PRIMARY KEY,
            country VARCHAR(100) NOT NULL COMMENT '国家',
            infected_num INT NOT NULL DEFAULT 0 COMMENT '感染数量',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
            UNIQUE KEY unique_country (country),
            INDEX idx_country (country),
            INDEX idx_updated (updated_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='全球僵尸网络统计表'
    """)
    print(f"   [+] {global_table} 表结构已确认")
    
    # 3. 重新聚合中国数据（按IP去重）
    print("\n[+] 重新聚合中国数据...")
    cursor.execute(f"""
        INSERT INTO {china_table} (province, municipality, infected_num, created_at, updated_at)
        SELECT 
            CASE
                -- 统一地名：去除各种后缀
                WHEN province LIKE '%壮族自治区' THEN REPLACE(province, '壮族自治区', '')
                WHEN province LIKE '%回族自治区' THEN REPLACE(province, '回族自治区', '')
                WHEN province LIKE '%维吾尔自治区' THEN REPLACE(province, '维吾尔自治区', '')
                WHEN province LIKE '%自治区' THEN REPLACE(province, '自治区', '')
                WHEN province LIKE '%省' THEN REPLACE(province, '省', '')
                WHEN province IN ('北京市', '天津市', '上海市', '重庆市') THEN REPLACE(province, '市', '')
                WHEN province IS NOT NULL THEN province
                ELSE '未知'
            END as province,
            CASE 
                WHEN city IN ('北京', '天津', '上海', '重庆') THEN city
                WHEN city IS NOT NULL THEN TRIM(TRAILING '市' FROM city)
                ELSE '未知'
            END as municipality,
            COUNT(DISTINCT ip) as infected_num,
            MIN(created_time) as created_at,
            MAX(updated_at) as updated_at
        FROM {node_table}
        WHERE country = '中国'
        GROUP BY 
            CASE
                WHEN province LIKE '%壮族自治区' THEN REPLACE(province, '壮族自治区', '')
                WHEN province LIKE '%回族自治区' THEN REPLACE(province, '回族自治区', '')
                WHEN province LIKE '%维吾尔自治区' THEN REPLACE(province, '维吾尔自治区', '')
                WHEN province LIKE '%自治区' THEN REPLACE(province, '自治区', '')
                WHEN province LIKE '%省' THEN REPLACE(province, '省', '')
                WHEN province IN ('北京市', '天津市', '上海市', '重庆市') THEN REPLACE(province, '市', '')
                WHEN province IS NOT NULL THEN province
                ELSE '未知'
            END,
            CASE 
                WHEN city IN ('北京', '天津', '上海', '重庆') THEN city
                WHEN city IS NOT NULL THEN TRIM(TRAILING '市' FROM city)
                ELSE '未知'
            END
    """)
    china_rows = cursor.rowcount
    print(f"   [+] 插入 {china_rows} 条中国统计记录")
    
    # 4. 重新聚合全球数据（按IP去重）
    print("\n[+] 重新聚合全球数据...")
    cursor.execute(f"""
        INSERT INTO {global_table} (country, infected_num, created_at, updated_at)
        SELECT 
            CASE
                -- 统一国家名称
                WHEN country = '中国台湾' THEN '台湾'
                WHEN country = '中国香港' THEN '香港'
                WHEN country = '中国澳门' THEN '澳门'
                WHEN country IS NOT NULL THEN country
                ELSE '未知'
            END as country,
            COUNT(DISTINCT ip) as infected_num,
            MIN(created_time) as created_at,
            MAX(updated_at) as updated_at
        FROM {node_table}
        GROUP BY 
            CASE
                WHEN country = '中国台湾' THEN '台湾'
                WHEN country = '中国香港' THEN '香港'
                WHEN country = '中国澳门' THEN '澳门'
                WHEN country IS NOT NULL THEN country
                ELSE '未知'
            END
    """)
    global_rows = cursor.rowcount
    print(f"   [+] 插入 {global_rows} 条全球统计记录")
    
    # 5. 验证数据一致性
    print("\n[*] 验证数据一致性...")
    
    # 从原始表统计唯一IP
    cursor.execute(f"SELECT COUNT(DISTINCT ip) as total FROM {node_table}")
    original_total = cursor.fetchone()['total']
    
    # 从聚合表统计
    cursor.execute(f"SELECT SUM(infected_num) as total FROM {global_table}")
    global_total = cursor.fetchone()['total'] or 0
    
    cursor.execute(f"SELECT SUM(infected_num) as total FROM {china_table}")
    china_total = cursor.fetchone()['total'] or 0
    
    # 中国在global_table中的数量
    cursor.execute(f"SELECT infected_num FROM {global_table} WHERE country = '中国'")
    china_in_global = cursor.fetchone()
    china_in_global_num = china_in_global['infected_num'] if china_in_global else 0
    
    # 其他国家的数量
    other_countries_total = global_total - china_in_global_num
    
    # 总计应该等于：中国表总数 + 其他国家总数
    calculated_total = china_total + other_countries_total
    
    print(f"   [+] 原始表唯一IP数: {original_total:,}")
    print(f"   [+] 全球聚合表总数: {global_total:,}")
    print(f"   [+] 中国聚合表总数: {china_total:,}")
    print(f"   [+] 其他国家总数: {other_countries_total:,}")
    print(f"   [+] 计算总数: {calculated_total:,}")
    
    # 检查差异
    diff = abs(original_total - global_total)
    if diff == 0:
        print(f"   [+] 数据完全一致")
    elif diff <= 10:
        print(f"   [!] 轻微差异: {diff} ({diff/original_total*100:.2f}%)")
        print(f"      (可能由于地理位置未标注或NULL值导致)")
    else:
        print(f"   [!] 数据不一致: 差异 {diff} ({diff/original_total*100:.2f}%)")
    
    return {
        'original_total': original_total,
        'global_total': global_total,
        'china_total': china_total,
        'china_rows': china_rows,
        'global_rows': global_rows
    }

def main():
    import argparse
    import io
    import sys
    
    # 设置UTF-8输出，避免Windows编码问题
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    
    parser = argparse.ArgumentParser(description='重建聚合表工具')
    parser.add_argument('--botnet', type=str, 
                       help='指定僵尸网络类型（默认处理所有）')
    
    args = parser.parse_args()
    
    # 确定要处理的僵尸网络列表
    botnets = [args.botnet] if args.botnet else BOTNET_TYPES
    
    print("\n" + "="*60)
    print("[*] 聚合表重建工具")
    print("="*60)
    print(f"处理范围: {', '.join(botnets)}")
    print("="*60)
    
    conn = None
    cursor = None
    
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        results = {}
        
        for botnet_type in botnets:
            result = rebuild_aggregation_tables(cursor, botnet_type)
            if result:
                results[botnet_type] = result
            
            conn.commit()
            print(f"[+] {botnet_type} 的聚合表已提交")
        
        # 总结
        print("\n" + "="*60)
        print("[*] 重建完成总结")
        print("="*60)
        
        for botnet_type, result in results.items():
            print(f"\n【{botnet_type.upper()}】")
            print(f"  原始唯一IP: {result['original_total']:,}")
            print(f"  全球聚合总数: {result['global_total']:,}")
            print(f"  中国聚合总数: {result['china_total']:,}")
            print(f"  中国统计行数: {result['china_rows']:,}")
            print(f"  全球统计行数: {result['global_rows']:,}")
        
        print("\n" + "="*60)
        print("[!] 所有聚合表重建完成！")
        print("="*60)
        
    except Exception as e:
        print(f"\n[!] 错误: {e}")
        if conn:
            conn.rollback()
            print("已回滚事务")
        raise
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    main()
