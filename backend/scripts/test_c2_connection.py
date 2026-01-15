#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
C2连接测试工具
用于诊断日志处理器无法连接C2的问题
"""

import sys
import os
import asyncio
import aiohttp

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import C2_ENDPOINTS

async def test_c2_endpoint(c2_config):
    """测试单个C2端点"""
    name = c2_config['name']
    url = c2_config['url']
    api_key = c2_config['api_key']
    
    print(f"\n{'='*60}")
    print(f"测试 C2端点: {name}")
    print(f"{'='*60}")
    print(f"URL: {url}")
    print(f"API Key: {api_key[:10]}...{api_key[-10:]}")
    print(f"Enabled: {c2_config.get('enabled', True)}")
    
    # 测试连接
    timeout = aiohttp.ClientTimeout(total=10)
    
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            # 测试1: 基础连接
            print(f"\n[测试1] 基础连接测试...")
            test_url = f"{url}/api/pull"
            print(f"请求URL: {test_url}")
            
            try:
                async with session.get(
                    test_url,
                    params={'limit': 10, 'confirm': 'false'},
                    headers={
                        'X-API-Key': api_key,
                        'User-Agent': 'C2ConnectionTest/1.0'
                    }
                ) as response:
                    print(f"✅ HTTP状态码: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ 响应格式: JSON")
                        print(f"✅ Success字段: {data.get('success')}")
                        print(f"✅ 数据条数: {len(data.get('data', []))}")
                        
                        if data.get('success'):
                            print(f"\n✅ C2端点工作正常!")
                            return True
                        else:
                            print(f"\n❌ C2返回错误: {data.get('error')}")
                            return False
                    
                    elif response.status == 401:
                        print(f"❌ 认证失败! API Key可能不正确")
                        print(f"   配置的API Key: {api_key}")
                        return False
                    
                    else:
                        text = await response.text()
                        print(f"❌ 请求失败")
                        print(f"   响应内容: {text[:200]}")
                        return False
                        
            except asyncio.TimeoutError:
                print(f"❌ 连接超时 (10秒)")
                print(f"   可能原因:")
                print(f"   1. C2服务未运行")
                print(f"   2. 端口被防火墙阻止")
                print(f"   3. URL配置错误")
                return False
                
            except aiohttp.ClientConnectorError as e:
                print(f"❌ 连接失败: {e}")
                print(f"   可能原因:")
                print(f"   1. C2服务未在 {url} 运行")
                print(f"   2. 端口未监听")
                print(f"   3. 防火墙阻止")
                return False
                
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主函数"""
    print("="*60)
    print("C2连接测试工具")
    print("="*60)
    
    if not C2_ENDPOINTS:
        print("\n❌ 没有配置C2端点!")
        print("   请检查 config.py 中的 C2_ENDPOINTS 配置")
        return
    
    print(f"\n找到 {len(C2_ENDPOINTS)} 个C2端点配置")
    
    results = []
    for c2 in C2_ENDPOINTS:
        if not c2.get('enabled', True):
            print(f"\n⚠️  跳过禁用的端点: {c2['name']}")
            continue
        
        result = await test_c2_endpoint(c2)
        results.append((c2['name'], result))
    
    # 总结
    print(f"\n{'='*60}")
    print("测试总结")
    print(f"{'='*60}")
    
    for name, result in results:
        status = "✅ 正常" if result else "❌ 失败"
        print(f"{name}: {status}")
    
    # 诊断建议
    failed_count = sum(1 for _, r in results if not r)
    if failed_count > 0:
        print(f"\n{'='*60}")
        print("诊断建议")
        print(f"{'='*60}")
        print(f"\n有 {failed_count} 个端点连接失败，请检查:")
        print(f"")
        print(f"1. 确认C2服务是否在运行:")
        print(f"   cd backend/remote")
        print(f"   python c2_data_server.py")
        print(f"")
        print(f"2. 检查端口是否监听:")
        print(f"   netstat -ano | findstr :8888")
        print(f"")
        print(f"3. 检查API Key是否匹配:")
        print(f"   - C2端: backend/remote/config.json 中的 api_key")
        print(f"   - 平台端: backend/config.py 中的 C2_ENDPOINTS[].api_key")
        print(f"")
        print(f"4. 检查URL是否正确:")
        print(f"   默认应该是: http://localhost:8888")
    else:
        print(f"\n✅ 所有C2端点连接正常!")
        print(f"\n如果日志处理器仍然无法拉取数据，请检查:")
        print(f"1. 日志处理器是否正确启动")
        print(f"2. 查看日志处理器日志: backend/logs/log_processor.log")
        print(f"3. 运行诊断: python backend/scripts/check_queue_status.py")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n测试已取消")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
