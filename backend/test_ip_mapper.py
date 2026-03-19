# -*- coding: utf-8 -*-
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import DB_CONFIG
from utils.ip_unit_industry_mapper import get_ip_unit_industry_mapper

print("=" * 70)
print("Testing IP-Unit-Industry Mapper")
print("=" * 70)

try:
    print("\n1. Creating mapper instance...")
    mapper = get_ip_unit_industry_mapper(DB_CONFIG)
    print("   OK Mapper created")
    
    print("\n2. Checking table and fields...")
    print(f"   Table exists: {mapper._table_exists}")
    print(f"   IP field: {mapper._ip_field}")
    print(f"   Has unit field: {mapper.has_unit_field()}")
    if mapper._unit_field:
        print(f"   Unit field name: {mapper._unit_field}")
    print(f"   Has industry field: {mapper.has_industry_field()}")
    if mapper._industry_field:
        print(f"   Industry field name: {mapper._industry_field}")
    
    print("\n3. Loading cache...")
    mapper._load_cache()
    print(f"   OK Cache loaded: {len(mapper._cache)} records")
    
    if len(mapper._cache) > 0:
        print("\n4. Testing queries...")
        # Get first 5 IPs from cache
        test_ips = list(mapper._cache.keys())[:5]
        
        for ip in test_ips:
            unit, industry = mapper.get_unit_industry(ip)
            print(f"   IP: {ip:<20} Unit: {unit or '(none)':<30} Industry: {industry or '(none)'}")
    
    print("\n" + "=" * 70)
    print("Test completed successfully!")
    print("=" * 70)
    
except Exception as e:
    print(f"\nError: {e}")
    import traceback
    traceback.print_exc()
