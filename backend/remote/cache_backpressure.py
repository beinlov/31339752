#!/usr/bin/env python3
"""
缓存背压控制模块
动态调整日志读取速度，防止缓存无限增长
"""

import logging
from typing import Dict, Tuple

logger = logging.getLogger(__name__)


class BackpressureController:
    """
    背压控制器 - 根据缓存量动态调整读取行为
    
    策略：
    1. 缓存 >= 高水位线 → 暂停读取（返回0）
    2. 缓存 <= 低水位线 → 全速读取（返回max_batch）
    3. 缓存在中间       → 线性缩放读取量
    """
    
    def __init__(self, config: Dict):
        """
        Args:
            config: 配置字典，包含：
                - max_cached_records: 最大缓存记录数（硬限制）
                - high_watermark: 高水位线（暂停读取阈值）
                - low_watermark: 低水位线（全速读取阈值）
                - read_batch_size: 基础读取批量大小
                - adaptive_read: 是否启用自适应读取（默认True）
        """
        self.max_cached = config.get('max_cached_records', 10000)
        self.high_watermark = config.get('high_watermark', int(self.max_cached * 0.8))
        self.low_watermark = config.get('low_watermark', int(self.max_cached * 0.2))
        self.read_batch_size = config.get('read_batch_size', 5000)
        self.adaptive_read = config.get('adaptive_read', True)
        
        # 统计信息
        self.total_paused = 0
        self.total_throttled = 0
        self.total_full_speed = 0
        
        logger.info(f"背压控制器初始化:")
        logger.info(f"  - 最大缓存: {self.max_cached} 条")
        logger.info(f"  - 高水位线: {self.high_watermark} 条")
        logger.info(f"  - 低水位线: {self.low_watermark} 条")
        logger.info(f"  - 基础读取量: {self.read_batch_size} 条")
        logger.info(f"  - 自适应模式: {self.adaptive_read}")
    
    def calculate_read_size(self, current_cached: int) -> Tuple[int, str]:
        """
        计算本次应该读取的记录数
        
        Args:
            current_cached: 当前缓存的记录数
        
        Returns:
            (read_size, reason) - 读取数量和原因
        """
        if not self.adaptive_read:
            # 简单模式：超过最大值就不读
            if current_cached >= self.max_cached:
                self.total_paused += 1
                return 0, f"缓存已满({current_cached}/{self.max_cached})"
            else:
                self.total_full_speed += 1
                return self.read_batch_size, "正常读取"
        
        # 自适应模式
        if current_cached >= self.high_watermark:
            # 高水位：暂停读取
            self.total_paused += 1
            return 0, f"背压暂停({current_cached}/{self.high_watermark})"
        
        elif current_cached <= self.low_watermark:
            # 低水位：全速读取
            self.total_full_speed += 1
            return self.read_batch_size, f"全速读取({current_cached}/{self.low_watermark})"
        
        else:
            # 中间水位：线性缩放
            # 计算缩放因子：从低水位的100%到高水位的0%
            available_range = self.high_watermark - self.low_watermark
            current_offset = current_cached - self.low_watermark
            scale_factor = 1.0 - (current_offset / available_range)
            
            read_size = int(self.read_batch_size * scale_factor)
            read_size = max(100, read_size)  # 至少读100条
            
            self.total_throttled += 1
            return read_size, f"节流读取({current_cached}条,缩放{scale_factor:.1%})"
    
    def should_skip_read(self, current_cached: int) -> Tuple[bool, str]:
        """
        判断是否应该跳过本次读取
        
        Returns:
            (should_skip, reason)
        """
        read_size, reason = self.calculate_read_size(current_cached)
        return read_size == 0, reason
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        total_decisions = self.total_paused + self.total_throttled + self.total_full_speed
        
        if total_decisions == 0:
            return {
                'total_decisions': 0,
                'paused_rate': '0%',
                'throttled_rate': '0%',
                'full_speed_rate': '0%'
            }
        
        return {
            'total_decisions': total_decisions,
            'paused_count': self.total_paused,
            'throttled_count': self.total_throttled,
            'full_speed_count': self.total_full_speed,
            'paused_rate': f"{self.total_paused/total_decisions*100:.1f}%",
            'throttled_rate': f"{self.total_throttled/total_decisions*100:.1f}%",
            'full_speed_rate': f"{self.total_full_speed/total_decisions*100:.1f}%"
        }
    
    def log_stats(self):
        """输出统计信息"""
        stats = self.get_stats()
        if stats['total_decisions'] > 0:
            logger.info(f"背压统计: 暂停{stats['paused_rate']}, 节流{stats['throttled_rate']}, 全速{stats['full_speed_rate']}")


# 使用示例
if __name__ == '__main__':
    # 配置
    config = {
        'max_cached_records': 10000,
        'high_watermark': 8000,
        'low_watermark': 2000,
        'read_batch_size': 5000,
        'adaptive_read': True
    }
    
    controller = BackpressureController(config)
    
    # 模拟不同缓存量
    test_cases = [0, 1000, 2000, 3000, 5000, 7000, 8000, 9000, 10000]
    
    print("\n背压控制测试:")
    print("="*60)
    for cached in test_cases:
        read_size, reason = controller.calculate_read_size(cached)
        print(f"缓存: {cached:5d} 条 → 读取: {read_size:4d} 条 ({reason})")
    
    print("\n" + "="*60)
    controller.log_stats()
