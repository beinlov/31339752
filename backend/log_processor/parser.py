"""
日志解析器模块
支持多种日志格式:
1. CSV格式: timestamp,ip,event_type,extra1,extra2,...
2. Ramnit格式: YYYY/MM/DD HH:MM:SS 事件描述: IP
3. 其他自定义格式
"""
import logging
import re
from typing import Dict, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class LogParser:
    """日志解析器"""
    
    def __init__(self, botnet_type: str, important_events: List[str] = None):
        """
        初始化日志解析器
        
        Args:
            botnet_type: 僵尸网络类型
            important_events: 需要保存到数据库的事件类型列表
        """
        self.botnet_type = botnet_type
        self.important_events = important_events or []
        
    def parse_line(self, line: str) -> Optional[Dict]:
        """
        解析单行日志 - 自动检测格式
        
        Args:
            line: 日志行内容
            
        Returns:
            解析后的字典，如果解析失败返回None
        """
        try:
            line = line.strip()
            if not line:
                return None
            
            # 跳过系统消息和分隔符
            if self._is_system_message(line):
                return None
                
            # 尝试不同的解析方法
            parsed_data = None
            
            # 1. 尝试Ramnit格式: "YYYY/MM/DD HH:MM:SS 事件描述: IP"
            if self.botnet_type == 'ramnit':
                parsed_data = self._parse_ramnit_format(line)
            
            # 2. 如果Ramnit格式失败,或者是其他类型,尝试CSV格式
            if not parsed_data:
                parsed_data = self._parse_csv_format(line)
            
            # 3. 如果都失败,尝试通用格式
            if not parsed_data:
                parsed_data = self._parse_generic_format(line)
                
            return parsed_data
            
        except Exception as e:
            logger.error(f"[{self.botnet_type}] Error parsing line: {e}, line: {line[:100]}")
            return None
    
    def _is_system_message(self, line: str) -> bool:
        """判断是否为系统消息(不需要解析的行)"""
        # 跳过分隔符
        if line.startswith('---') or line.startswith('==='):
            return True
        # 跳过服务器启动消息
        if '服务器' in line and ('启动' in line or '监听' in line or 'worker' in line):
            return True
        return False
    
    def _parse_ramnit_format(self, line: str) -> Optional[Dict]:
        """
        解析Ramnit格式日志
        格式: YYYY/MM/DD HH:MM:SS 事件描述: IP
        例如: 2025/07/03 09:31:24 新IP首次连接: 180.254.163.108
        """
        try:
            # 正则匹配: 日期 时间 事件描述: IP
            pattern = r'^(\d{4}/\d{2}/\d{2}\s+\d{2}:\d{2}:\d{2})\s+(.+?):\s+(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})$'
            match = re.match(pattern, line)
            
            if match:
                timestamp_str = match.group(1)
                event_desc = match.group(2).strip()
                ip = match.group(3)
                
                # 验证IP
                if not self._is_valid_ip(ip):
                    return None
                
                # 转换时间格式: YYYY/MM/DD HH:MM:SS -> YYYY-MM-DD HH:MM:SS
                try:
                    dt = datetime.strptime(timestamp_str, '%Y/%m/%d %H:%M:%S')
                    timestamp = dt.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    timestamp = timestamp_str.replace('/', '-')
                
                # 确定事件类型
                event_type = self._extract_event_type(event_desc)
                
                parsed_data = {
                    'timestamp': timestamp,
                    'ip': ip,
                    'event_type': event_type,
                    'extras': [event_desc],
                    'botnet_type': self.botnet_type,
                    'raw_line': line
                }
                
                return parsed_data
            
            return None
            
        except Exception as e:
            logger.debug(f"[{self.botnet_type}] Not Ramnit format: {line[:50]}")
            return None
    
    def _parse_csv_format(self, line: str) -> Optional[Dict]:
        """
        解析CSV格式日志
        格式: timestamp,ip,event_type,extra1,extra2,...
        """
        try:
            # 按逗号分割
            parts = line.split(',')
            
            # 至少需要3个字段: timestamp, ip, event_type
            if len(parts) < 3:
                return None
                
            parsed_data = {
                'timestamp': parts[0].strip(),
                'ip': parts[1].strip(),
                'event_type': parts[2].strip(),
                'extras': [p.strip() for p in parts[3:]] if len(parts) > 3 else [],
                'botnet_type': self.botnet_type,
                'raw_line': line
            }
            
            # 验证IP格式
            if not self._is_valid_ip(parsed_data['ip']):
                return None
                
            return parsed_data
            
        except Exception as e:
            return None
    
    def _parse_generic_format(self, line: str) -> Optional[Dict]:
        """
        通用格式解析 - 尝试从行中提取IP地址
        """
        try:
            # 使用正则查找IP地址
            ip_pattern = r'\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b'
            ip_matches = re.findall(ip_pattern, line)
            
            if not ip_matches:
                return None
            
            # 取第一个有效IP
            ip = None
            for potential_ip in ip_matches:
                if self._is_valid_ip(potential_ip):
                    ip = potential_ip
                    break
            
            if not ip:
                return None
            
            # 尝试提取时间戳
            timestamp = self._extract_timestamp(line)
            if not timestamp:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            parsed_data = {
                'timestamp': timestamp,
                'ip': ip,
                'event_type': 'connection',  # 默认事件类型
                'extras': [line],
                'botnet_type': self.botnet_type,
                'raw_line': line
            }
            
            return parsed_data
            
        except Exception as e:
            return None
    
    def _extract_timestamp(self, line: str) -> Optional[str]:
        """从行中提取时间戳"""
        # 尝试多种时间格式
        patterns = [
            (r'(\d{4}/\d{2}/\d{2}\s+\d{2}:\d{2}:\d{2})', '%Y/%m/%d %H:%M:%S', '%Y-%m-%d %H:%M:%S'),
            (r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M:%S'),
            (r'(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2})', '%d/%m/%Y %H:%M:%S', '%Y-%m-%d %H:%M:%S'),
        ]
        
        for pattern, input_fmt, output_fmt in patterns:
            match = re.search(pattern, line)
            if match:
                try:
                    dt = datetime.strptime(match.group(1), input_fmt)
                    return dt.strftime(output_fmt)
                except:
                    continue
        
        return None
    
    def _extract_event_type(self, description: str) -> str:
        """从事件描述中提取事件类型"""
        # 关键词映射
        keywords_map = {
            '首次连接': 'first_connection',
            '新IP': 'new_ip',
            '连接': 'connection',
            '断开': 'disconnect',
            '上传': 'upload',
            '下载': 'download',
            '命令': 'command',
            '心跳': 'heartbeat',
        }
        
        for keyword, event_type in keywords_map.items():
            if keyword in description:
                return event_type
        
        return 'unknown'
            
    def should_save_to_db(self, parsed_data: Dict) -> bool:
        """
        判断是否需要保存到数据库
        
        Args:
            parsed_data: 解析后的数据
            
        Returns:
            是否需要保存
        """
        if not parsed_data:
            return False
            
        # 如果没有配置重要事件列表，则保存所有事件
        if not self.important_events:
            return True
            
        # 检查事件类型是否在重要事件列表中
        event_type = parsed_data.get('event_type', '').lower()
        return event_type in [e.lower() for e in self.important_events]
        
    @staticmethod
    def _is_valid_ip(ip: str) -> bool:
        """
        简单的IP地址格式验证
        
        Args:
            ip: IP地址字符串
            
        Returns:
            是否为有效IP
        """
        try:
            parts = ip.split('.')
            if len(parts) != 4:
                return False
            for part in parts:
                num = int(part)
                if num < 0 or num > 255:
                    return False
            return True
        except:
            return False
            
    def extract_command(self, parsed_data: Dict) -> Optional[str]:
        """
        从解析数据中提取命令信息（针对asruex等有命令的僵尸网络）
        
        Args:
            parsed_data: 解析后的数据
            
        Returns:
            命令字符串或None
        """
        if not parsed_data or not parsed_data.get('extras'):
            return None
            
        # 针对asruex格式: timestamp,ip,event_type,url
        # 从URL中提取 ?ql=xx 格式的命令
        if self.botnet_type == 'asruex' and parsed_data.get('extras'):
            url = parsed_data['extras'][0] if parsed_data['extras'] else ''
            if '?ql=' in url:
                try:
                    command = url.split('?ql=')[-1][:2]  # 取ql=后面的2个字符
                    return command
                except:
                    pass
                    
        return None
        
    def get_description(self, parsed_data: Dict) -> str:
        """
        获取事件描述（针对有命令字典的僵尸网络）
        
        Args:
            parsed_data: 解析后的数据
            
        Returns:
            事件描述
        """
        # asruex命令描述字典
        asruex_descriptions = {
            'b2': "蠕虫程序刚运行，首次请求验证C2有效性",
            'a0': "上传文件前请求，疑似建议服务器新建目录",
            'a1': "询问文件名是否可以删除",
            'a4': "POST文件",
            'a5': "蠕虫查命令列表",
            'a3': "客户端用param1查命令文件列表",
            'a7': "客户端下载文件后访问",
            'a6': "客户端a7下载后，提示已保存完成",
            'a8': "询问文件名是否可以删除",
            'a9': "蠕虫查命令列表，下一步会用b0下载",
            'b0': "下载",
            'b1': "确认下载"
        }
        
        if self.botnet_type == 'asruex':
            command = self.extract_command(parsed_data)
            if command and command in asruex_descriptions:
                return asruex_descriptions[command]
                
        return parsed_data.get('event_type', 'Unknown event')


