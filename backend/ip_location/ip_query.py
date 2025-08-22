# -*- coding:utf-8 -*-

from . import awdb
from awaits.awaitable import awaitable
import os
x = 12

@awaitable
def ip_query(ip):
    ip_info = dict()

    # filename = r'../ip_location/IP_city_single_WGS84.awdb'
    filename = os.path.dirname(__file__) + os.sep + 'IP_city_single_WGS84.awdb' #使用绝对路径
    reader = awdb.open_database(filename)
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
    
    async def main():
        ip = '171.34.246.78'
        ip_info = await ip_query(ip)
        
        print(ip_info)
        print(f"经度 (longitude): {ip_info.get('longitude')}")
        print(f"纬度 (latitude): {ip_info.get('latitude')}")
        print(__file__)
    
    asyncio.run(main())


