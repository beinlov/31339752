# -*- coding:utf-8 -*-

from . import awdb
from awaits.awaitable import awaitable
import os
x = 12

# 全局缓存 AWDB reader，只打开一次文件（线程安全）
_awdb_reader = None
_awdb_filename = None

def _get_awdb_reader():
    """获取或创建 AWDB reader（单例模式）"""
    global _awdb_reader, _awdb_filename
    
    filename = os.path.dirname(__file__) + os.sep + 'IP_city_single_WGS84.awdb'
    
    # 如果文件路径变了或还没初始化，重新打开
    if _awdb_reader is None or _awdb_filename != filename:
        _awdb_reader = awdb.open_database(filename)
        _awdb_filename = filename
    
    return _awdb_reader

@awaitable
def ip_query(ip):
    ip_info = dict()

    # 使用缓存的 reader，不再每次打开文件
    reader = _get_awdb_reader()
    try:
        (record, prefix_len) = reader.get_with_prefix_len(ip)

        continent = record.get("continent", b'').decode("utf-8") #大州
        country = record.get("country", b'').decode("utf-8") #国家
        province = record.get("province", b'').decode("utf-8") #省份
        city = record.get("city", b'').decode("utf-8") #城市
        country_prov_city = record.get("country_prov_city", b'').decode("utf-8") #国家_省份_城市
        isp = record.get("isp", b'').decode("utf-8")  #提供商，运营商
        asnumber = record.get("asnumber", b'').decode("utf-8") #AS编号
        longitude = record.get("lngwgs", b'').decode("utf-8") #经度
        latitude = record.get("latwgs", b'').decode("utf-8") #纬度  
        ip_info = {
            'continent':continent,
            'country':country,
            'province':province,
            'city':city,
            'isp':isp,
            'asn':asnumber,
            'prefix_len': str(prefix_len),
            'longitude': longitude,
            'latitude': latitude,
        }

        return ip_info
    except Exception as e:
        return ip_info

    # zipcode = record.get("zipcode", b'').decode("utf-8") #邮编
    # timezone = record.get("timezone", b'').decode("utf-8") #时区
    # accuracy = record.get("accuracy", b'').decode("utf-8") #定位精度，城市级
    # source = record.get("source", b'').decode("utf-8") #数据来源（采集方式），例如数据挖掘
    # owner = record.get("owner", b'').decode("utf-8") #IP拥有者名称
    # lngwgs = record.get("lngwgs", b'').decode("utf-8") #地理经度


    # print("大州:" + continent)
    # print("国家:" + country)
    # print('省份:'+province)
    # print('城市：'+city)
    # print("运营商:" + isp)
    # print("AS编号:" + asnumber)
    # print("网络前缀:" + str(prefix_len))

if __name__ == '__main__':
    import asyncio
    import time
    import random
    import sys
    import os
    
    # 添加父目录到path，解决相对导入问题
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    async def test_single_ip():
        """测试单个IP查询"""
        ip = '171.34.246.78'
        ip_info = await ip_query(ip)
        
        print("单个IP查询结果:")
        print(ip_info)
        print(f"经度 (longitude): {ip_info.get('longitude')}")
        print(f"纬度 (latitude): {ip_info.get('latitude')}")
        print()
    
    async def test_batch_ips(count=1000):
        """测试批量IP查询性能"""
        print(f"=" * 60)
        print(f"测试批量IP查询性能 - {count} 个IP")
        print(f"=" * 60)
        
        # 生成1000个随机IP
        test_ips = []
        for _ in range(count):
            ip = f"{random.randint(1,223)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"
            test_ips.append(ip)
        
        print(f"生成了 {len(test_ips)} 个测试IP")
        print(f"示例IP: {test_ips[:5]}")
        print()
        
        # 测试同步查询
        print("【方式1】逐个查询（串行）")
        start = time.time()
        success = 0
        for ip in test_ips:
            try:
                result = await ip_query(ip)
                if result.get('country'):
                    success += 1
            except Exception as e:
                pass
        sync_time = time.time() - start
        print(f"  耗时: {sync_time:.2f}秒")
        print(f"  成功: {success}/{count}")
        print(f"  速度: {count/sync_time:.0f} 个/秒")
        print()
        
        # 测试并发查询（批量）
        print("【方式2】并发查询（异步批量）")
        start = time.time()
        tasks = [ip_query(ip) for ip in test_ips]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        async_time = time.time() - start
        success = sum(1 for r in results if isinstance(r, dict) and r.get('country'))
        print(f"  耗时: {async_time:.2f}秒")
        print(f"  成功: {success}/{count}")
        print(f"  速度: {count/async_time:.0f} 个/秒")
        print()
        
        # 性能对比
        print(f"=" * 60)
        print(f"性能对比")
        print(f"=" * 60)
        print(f"串行查询: {sync_time:.2f}秒 ({count/sync_time:.0f} 个/秒)")
        print(f"并发查询: {async_time:.2f}秒 ({count/async_time:.0f} 个/秒)")
        if sync_time > async_time:
            speedup = sync_time / async_time
            print(f"并发提升: {speedup:.1f}x")
        print()
        
        # 估算处理1000条数据的IP增强时间
        print(f"=" * 60)
        print(f"估算Worker中的IP增强时间")
        print(f"=" * 60)
        print(f"1000个IP增强预计耗时: {async_time:.2f}秒")
        print(f"加上数据库写入时间: ~{async_time + 2:.2f}秒")
        print(f"Worker总耗时预计: ~{async_time + 3:.2f}秒")
        print()
    
    async def main():
        # 测试单个IP
        await test_single_ip()
        
        # 测试1000个IP的性能
        await test_batch_ips(1000)
        
        print(f"测试文件位置: {__file__}")
    
    asyncio.run(main())


