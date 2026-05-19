#!/usr/bin/env python3
"""
中继节点数据服务器
功能：
1. 从C2端拉取数据并本地缓存
2. 提供HTTP API供平台服务器拉取数据
3. 支持两阶段提交和断点续传
4. 预留推送接收接口（未来扩展）
"""

import asyncio
import json
import logging
import os
import signal
import sys
import ssl
from datetime import datetime
from typing import Dict, List, Optional
from aiohttp import web
import threading

# 导入本地模块
from data_puller import DataPuller
from data_storage import DataStorage
from config_loader import load_config, validate_config

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s',
    handlers=[
        logging.FileHandler('relay_node.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class RelayDataServer:
    """中继节点数据服务器"""
    
    def __init__(self, config_file: str = 'relay_node_config.json'):
        """初始化服务器"""
        self.config = load_config(config_file)
        
        # 验证配置
        if not validate_config(self.config):
            raise ValueError("配置验证失败")
        
        # 初始化存储
        storage_config = self.config.get('storage', {})
        self.storage = DataStorage(
            db_file=storage_config.get('db_file', './relay_node_cache.db'),
            retention_days=storage_config.get('retention_days', 7)
        )
        
        # 初始化拉取器
        puller_config = self.config.get('puller', {})
        self.puller = DataPuller(puller_config)
        
        # 服务器配置
        server_config = self.config.get('server', {})
        self.host = server_config.get('host', '0.0.0.0')
        self.port = server_config.get('port', 8888)
        self.api_key = server_config.get('api_key', '')
        self.use_https = server_config.get('use_https', False)
        self.ssl_cert = server_config.get('ssl_cert', './cert.pem')
        self.ssl_key = server_config.get('ssl_key', './key.pem')
        
        # 间隔配置
        intervals = self.config.get('intervals', {})
        self.pull_interval = intervals.get('pull', 10)
        self.cleanup_interval = intervals.get('cleanup', 3600)
        
        # 运行状态
        self.running = False
        self.app = None
        
        # 统计信息
        self.stats = {
            'start_time': None,
            'total_pulled': 0,
            'total_served': 0,
            'last_pull_time': None,
            'last_serve_time': None
        }
        
        logger.info("=" * 70)
        logger.info("中继节点服务器初始化完成")
        logger.info("=" * 70)
        logger.info(f"监听地址: {self.host}:{self.port}")
        logger.info(f"使用HTTPS: {self.use_https}")
        logger.info(f"C2服务器数量: {len(self.puller.c2_servers)}")
        logger.info(f"拉取间隔: {self.pull_interval} 秒")
        logger.info(f"数据保留: {self.storage.retention_days} 天")
        logger.info("=" * 70)
    
    def _check_api_key(self, request: web.Request) -> bool:
        """检查API密钥"""
        if not self.api_key:
            return True
        
        provided_key = request.headers.get('X-API-Key', '')
        return provided_key == self.api_key
    
    async def handle_health(self, request: web.Request) -> web.Response:
        """健康检查接口"""
        if not self._check_api_key(request):
            return web.json_response({'error': 'Unauthorized'}, status=401)
        
        stats = self.storage.get_statistics()
        c2_health = self.puller.check_all_servers()
        
        return web.json_response({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'storage': stats,
            'c2_servers': c2_health,
            'uptime_seconds': (datetime.now() - self.stats['start_time']).total_seconds() if self.stats['start_time'] else 0
        })
    
    async def handle_stats(self, request: web.Request) -> web.Response:
        """统计信息接口"""
        if not self._check_api_key(request):
            return web.json_response({'error': 'Unauthorized'}, status=401)
        
        stats = self.storage.get_statistics()
        
        return web.json_response({
            'storage': stats,
            'service': {
                'total_pulled': self.stats['total_pulled'],
                'total_served': self.stats['total_served'],
                'last_pull_time': self.stats['last_pull_time'],
                'last_serve_time': self.stats['last_serve_time'],
                'uptime_seconds': (datetime.now() - self.stats['start_time']).total_seconds() if self.stats['start_time'] else 0
            },
            'timestamp': datetime.now().isoformat()
        })
    
    async def handle_pull(self, request: web.Request) -> web.Response:
        """
        数据拉取接口（供平台服务器调用）
        
        Query参数：
        - limit: 最大返回数量（默认1000）
        - confirm: 是否立即确认删除（默认false，两阶段提交）
        - since_seq: 断点续传起始序列号
        """
        if not self._check_api_key(request):
            return web.json_response({'error': 'Unauthorized'}, status=401)
        
        try:
            # 解析参数
            limit = int(request.query.get('limit', 1000))
            confirm = request.query.get('confirm', 'false').lower() == 'true'
            since_seq = request.query.get('since_seq')
            if since_seq:
                since_seq = int(since_seq)
            
            # 限制最大拉取量
            limit = min(limit, 5000)
            
            # 从存储获取数据
            records, max_seq_id = self.storage.get_pending_data(
                limit=limit,
                since_seq=since_seq
            )
            
            count = len(records)
            
            # 如果立即确认，标记为已提供
            if confirm and count > 0:
                self.storage.mark_as_served(count)
            
            # 更新统计
            self.stats['total_served'] += count
            self.stats['last_serve_time'] = datetime.now().isoformat()
            
            logger.info(f"✅ 平台拉取数据: {count} 条 (confirm={confirm}, since_seq={since_seq})")
            
            return web.json_response({
                'success': True,
                'count': count,
                'data': records,
                'max_seq_id': max_seq_id,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"❌ 拉取请求处理失败: {e}", exc_info=True)
            return web.json_response({
                'success': False,
                'error': str(e)
            }, status=500)
    
    async def handle_confirm(self, request: web.Request) -> web.Response:
        """
        确认接口（两阶段提交）
        平台确认已成功处理数据后，中继节点标记为已提供
        
        POST Body:
        {
            "count": 100  // 确认的记录数
        }
        """
        if not self._check_api_key(request):
            return web.json_response({'error': 'Unauthorized'}, status=401)
        
        try:
            data = await request.json()
            count = data.get('count', 0)
            
            if count <= 0:
                return web.json_response({
                    'success': False,
                    'error': 'Invalid count'
                }, status=400)
            
            # 标记为已提供
            updated = self.storage.mark_as_served(count)
            
            logger.info(f"✅ 平台确认: {updated} 条")
            
            return web.json_response({
                'success': True,
                'confirmed': updated,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"❌ 确认请求处理失败: {e}", exc_info=True)
            return web.json_response({
                'success': False,
                'error': str(e)
            }, status=500)
    
    async def handle_data_push(self, request: web.Request) -> web.Response:
        """
        数据推送接收接口（预留，未来扩展）
        用于接收动态IP资源池节点推送的数据
        
        POST Body:
        {
            "data": [...],
            "source": "dynamic-ip-pool-1"
        }
        """
        if not self._check_api_key(request):
            return web.json_response({'error': 'Unauthorized'}, status=401)
        
        # TODO: 未来实现
        return web.json_response({
            'success': False,
            'error': 'Push mode not implemented yet'
        }, status=501)
    
    def _setup_routes(self):
        """设置路由"""
        self.app = web.Application()
        self.app.router.add_get('/health', self.handle_health)
        self.app.router.add_get('/api/stats', self.handle_stats)
        self.app.router.add_get('/api/pull', self.handle_pull)
        self.app.router.add_post('/api/confirm', self.handle_confirm)
        self.app.router.add_post('/api/data-push', self.handle_data_push)  # 预留
        
        logger.info("HTTP路由设置完成")
    
    async def pull_task(self):
        """后台拉取任务"""
        logger.info("启动拉取任务")
        
        while self.running:
            try:
                # 从所有C2服务器拉取数据
                results = self.puller.pull_from_all_servers()
                
                for result in results:
                    server_config = result['server_config']
                    data = result['data']
                    
                    records = data.get('data', [])
                    if records:
                        # 保存到本地存储
                        saved = self.storage.save_pulled_data(
                            records,
                            c2_server=server_config.get('id', server_config['url'])
                        )
                        
                        # 更新统计
                        self.stats['total_pulled'] += saved
                        self.stats['last_pull_time'] = datetime.now().isoformat()
                        
                        # 两阶段提交：确认C2删除
                        if saved > 0:
                            self.puller.confirm_pull(server_config, saved)
                
                # 等待下次拉取
                await asyncio.sleep(self.pull_interval)
                
            except Exception as e:
                logger.error(f"拉取任务异常: {e}", exc_info=True)
                await asyncio.sleep(5)  # 错误后等待5秒
    
    async def cleanup_task(self):
        """后台清理任务"""
        logger.info("启动清理任务")
        
        while self.running:
            try:
                await asyncio.sleep(self.cleanup_interval)
                
                # 清理过期数据
                deleted = self.storage.cleanup_old_data()
                if deleted > 0:
                    logger.info(f"清理过期数据: {deleted} 条")
                
            except Exception as e:
                logger.error(f"清理任务异常: {e}", exc_info=True)
    
    async def start_background_tasks(self, app):
        """启动后台任务"""
        app['pull_task'] = asyncio.create_task(self.pull_task())
        app['cleanup_task'] = asyncio.create_task(self.cleanup_task())
    
    async def cleanup_background_tasks(self, app):
        """清理后台任务"""
        app['pull_task'].cancel()
        app['cleanup_task'].cancel()
        await asyncio.gather(
            app['pull_task'],
            app['cleanup_task'],
            return_exceptions=True
        )
    
    def run(self):
        """运行服务器"""
        self.running = True
        self.stats['start_time'] = datetime.now()
        
        # 设置路由
        self._setup_routes()
        
        # 设置后台任务
        self.app.on_startup.append(self.start_background_tasks)
        self.app.on_cleanup.append(self.cleanup_background_tasks)
        
        # 配置SSL（如果启用HTTPS）
        ssl_context = None
        if self.use_https:
            ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            ssl_context.load_cert_chain(self.ssl_cert, self.ssl_key)
            logger.info(f"启用HTTPS，证书: {self.ssl_cert}")
        
        # 启动服务器
        logger.info(f"启动HTTP{'S' if self.use_https else ''}服务器: {self.host}:{self.port}")
        web.run_app(
            self.app,
            host=self.host,
            port=self.port,
            ssl_context=ssl_context,
            access_log=None  # 禁用访问日志，使用自定义日志
        )
    
    def stop(self):
        """停止服务器"""
        self.running = False
        logger.info("服务器停止")


def main():
    """主函数"""
    # 解析命令行参数
    config_file = 'relay_node_config.json'
    if len(sys.argv) > 1:
        config_file = sys.argv[1]
    
    # 创建并运行服务器
    try:
        server = RelayDataServer(config_file)
        
        # 信号处理
        def signal_handler(sig, frame):
            logger.info("收到停止信号")
            server.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # 运行服务器
        server.run()
        
    except Exception as e:
        logger.error(f"服务器启动失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
