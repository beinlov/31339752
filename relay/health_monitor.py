#!/usr/bin/env python3
"""
中转服务器健康监控脚本
定期检查服务状态并发送告警
"""

import os
import sys
import time
import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

# 添加relay目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_puller import DataPuller
from data_pusher import DataPusher
from config_loader import load_config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


class HealthMonitor:
    """健康监控器"""
    
    def __init__(self, config_file: str = 'relay_config.json'):
        self.config = load_config(config_file)
        self.puller = DataPuller(self.config.get('puller', {}))
        self.pusher = DataPusher(self.config.get('pusher', {}))
        self.db_file = self.config.get('storage', {}).get('db_file', './relay_cache.db')
    
    def check_c2_servers(self) -> dict:
        """检查C2服务器健康状态"""
        logger.info("检查C2服务器...")
        results = self.puller.check_all_servers()
        
        healthy = sum(1 for v in results.values() if v)
        total = len(results)
        
        status = {
            'healthy': healthy,
            'total': total,
            'is_ok': healthy > 0,  # 至少一个C2健康
            'details': results
        }
        
        if status['is_ok']:
            logger.info(f"✅ C2服务器: {healthy}/{total} 健康")
        else:
            logger.error(f"❌ C2服务器: 所有服务器不健康!")
        
        return status
    
    def check_platform_server(self) -> dict:
        """检查平台服务器健康状态"""
        logger.info("检查平台服务器...")
        is_healthy = self.pusher.health_check()
        
        status = {
            'is_ok': is_healthy,
            'url': self.pusher.platform_url
        }
        
        if status['is_ok']:
            logger.info(f"✅ 平台服务器: 健康")
        else:
            logger.error(f"❌ 平台服务器: 不健康!")
        
        return status
    
    def check_database(self) -> dict:
        """检查本地数据库状态"""
        logger.info("检查本地数据库...")
        
        if not os.path.exists(self.db_file):
            logger.error(f"❌ 数据库文件不存在: {self.db_file}")
            return {'is_ok': False, 'error': '文件不存在'}
        
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                
                # 总记录数
                cursor.execute("SELECT COUNT(*) FROM data_records")
                total_records = cursor.fetchone()[0]
                
                # 待推送数
                cursor.execute("SELECT COUNT(*) FROM data_records WHERE status = 'pending'")
                pending_count = cursor.fetchone()[0]
                
                # 失败数
                cursor.execute("SELECT COUNT(*) FROM data_records WHERE status = 'failed'")
                failed_count = cursor.fetchone()[0]
                
                # 检查是否有长时间pending的记录
                one_hour_ago = (datetime.now() - timedelta(hours=1)).isoformat()
                cursor.execute("""
                    SELECT COUNT(*) FROM data_records 
                    WHERE status = 'pending' AND created_at < ?
                """, (one_hour_ago,))
                stale_pending = cursor.fetchone()[0]
                
                status = {
                    'is_ok': True,
                    'total_records': total_records,
                    'pending': pending_count,
                    'failed': failed_count,
                    'stale_pending': stale_pending
                }
                
                logger.info(f"✅ 数据库: 总计{total_records}条, 待推送{pending_count}条, 失败{failed_count}条")
                
                if stale_pending > 100:
                    logger.warning(f"⚠️  有{stale_pending}条数据超过1小时未推送")
                    status['warning'] = f'{stale_pending}条数据长时间pending'
                
                if failed_count > 1000:
                    logger.warning(f"⚠️  失败数据过多: {failed_count}条")
                    status['warning'] = f'失败数据过多: {failed_count}条'
                
                return status
                
        except Exception as e:
            logger.error(f"❌ 数据库检查失败: {e}")
            return {'is_ok': False, 'error': str(e)}
    
    def check_openvpn(self) -> dict:
        """检查OpenVPN连接状态"""
        logger.info("检查OpenVPN连接...")
        
        try:
            import subprocess
            
            # 检查OpenVPN进程
            result = subprocess.run(
                ['pgrep', '-f', 'openvpn'],
                capture_output=True,
                text=True
            )
            
            is_running = bool(result.stdout.strip())
            
            if is_running:
                # 检查tun0接口
                result = subprocess.run(
                    ['ip', 'addr', 'show', 'tun0'],
                    capture_output=True,
                    text=True
                )
                has_tun0 = result.returncode == 0
                
                status = {
                    'is_ok': has_tun0,
                    'process_running': is_running,
                    'tunnel_exists': has_tun0
                }
                
                if has_tun0:
                    logger.info("✅ OpenVPN: 运行中")
                else:
                    logger.warning("⚠️  OpenVPN进程运行但隧道未建立")
            else:
                logger.error("❌ OpenVPN: 未运行")
                status = {
                    'is_ok': False,
                    'process_running': False
                }
            
            return status
            
        except Exception as e:
            logger.error(f"❌ OpenVPN检查失败: {e}")
            return {'is_ok': False, 'error': str(e)}
    
    def check_disk_space(self) -> dict:
        """检查磁盘空间"""
        logger.info("检查磁盘空间...")
        
        try:
            import shutil
            
            total, used, free = shutil.disk_usage('/')
            free_percent = (free / total) * 100
            
            status = {
                'is_ok': free_percent > 10,  # 至少10%剩余空间
                'free_percent': round(free_percent, 2),
                'free_gb': round(free / (1024**3), 2)
            }
            
            if status['is_ok']:
                logger.info(f"✅ 磁盘空间: {status['free_percent']}% 可用 ({status['free_gb']} GB)")
            else:
                logger.error(f"❌ 磁盘空间不足: {status['free_percent']}%")
            
            return status
            
        except Exception as e:
            logger.error(f"❌ 磁盘检查失败: {e}")
            return {'is_ok': False, 'error': str(e)}
    
    def run_full_check(self) -> dict:
        """运行完整健康检查"""
        logger.info("\n" + "=" * 70)
        logger.info("开始健康检查")
        logger.info("=" * 70)
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'c2_servers': self.check_c2_servers(),
            'platform_server': self.check_platform_server(),
            'database': self.check_database(),
            'openvpn': self.check_openvpn(),
            'disk_space': self.check_disk_space()
        }
        
        # 总体状态
        all_ok = all(
            results[key].get('is_ok', False)
            for key in ['c2_servers', 'platform_server', 'database', 'openvpn', 'disk_space']
        )
        
        results['overall_status'] = 'healthy' if all_ok else 'unhealthy'
        
        logger.info("\n" + "=" * 70)
        if all_ok:
            logger.info("✅ 总体状态: 健康")
        else:
            logger.error("❌ 总体状态: 不健康")
            
            # 列出问题
            problems = []
            for key, value in results.items():
                if isinstance(value, dict) and not value.get('is_ok', True):
                    problems.append(key)
            
            logger.error(f"问题组件: {', '.join(problems)}")
        
        logger.info("=" * 70)
        
        return results
    
    def send_alert(self, results: dict):
        """发送告警（示例，可集成邮件/webhook等）"""
        if results['overall_status'] == 'unhealthy':
            logger.warning("⚠️  检测到健康问题，需要人工介入")
            # TODO: 集成告警系统（邮件、钉钉、Slack等）


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="中转服务器健康监控")
    parser.add_argument('--config', default='relay_config.json', help='配置文件路径')
    parser.add_argument('--loop', action='store_true', help='循环运行')
    parser.add_argument('--interval', type=int, default=300, help='检查间隔（秒）')
    args = parser.parse_args()
    
    try:
        monitor = HealthMonitor(config_file=args.config)
        
        if args.loop:
            logger.info(f"进入循环模式，间隔{args.interval}秒")
            while True:
                results = monitor.run_full_check()
                monitor.send_alert(results)
                time.sleep(args.interval)
        else:
            results = monitor.run_full_check()
            monitor.send_alert(results)
            
            # 返回退出码
            sys.exit(0 if results['overall_status'] == 'healthy' else 1)
            
    except KeyboardInterrupt:
        logger.info("\n收到中断信号")
        sys.exit(0)
    except Exception as e:
        logger.error(f"监控异常: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
