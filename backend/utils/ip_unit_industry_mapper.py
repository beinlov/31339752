# -*- coding: utf-8 -*-
import pymysql
from typing import Optional, Dict, Tuple
import logging

logger = logging.getLogger(__name__)

class IPUnitIndustryMapper:
    """IP-Unit-Industry Mapper with memory cache for performance"""
    
    def __init__(self, db_config: Dict):
        self.db_config = db_config
        self._cache = {}  # Memory cache: {ip: (unit, industry)}
        self._cache_loaded = False
        self._table_exists = None
        self._has_unit_field = None
        self._has_industry_field = None
        self._ip_field = None
    
    def _check_table_and_fields(self):
        """Check if ip_info table and fields exist"""
        if self._table_exists is not None:
            return
        
        try:
            conn = pymysql.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Check if table exists
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM information_schema.tables 
                WHERE table_schema = %s AND table_name = 'ip_info'
            """, (self.db_config['database'],))
            
            self._table_exists = cursor.fetchone()[0] > 0
            
            if not self._table_exists:
                logger.warning("ip_info table does not exist")
                self._has_unit_field = False
                self._has_industry_field = False
                return
            
            # Check all fields
            cursor.execute("""
                SELECT COLUMN_NAME
                FROM information_schema.columns
                WHERE table_schema = %s 
                AND table_name = 'ip_info'
            """, (self.db_config['database'],))
            
            existing_fields = {row[0] for row in cursor.fetchall()}
            
            # Detect IP field name (case insensitive)
            self._ip_field = None
            for field in existing_fields:
                if field.lower() == 'ip':
                    self._ip_field = field
                    break
            
            # Detect field names (support Chinese and English)
            self._has_unit_field = 'unit' in existing_fields or 'danwei' in existing_fields
            self._has_industry_field = 'industry' in existing_fields or 'hangye' in existing_fields
            
            # Determine actual field names
            self._unit_field = 'unit' if 'unit' in existing_fields else ('danwei' if 'danwei' in existing_fields else None)
            self._industry_field = 'industry' if 'industry' in existing_fields else ('hangye' if 'hangye' in existing_fields else None)
            
            logger.info(f"ip_info table check: unit={self._has_unit_field}, industry={self._has_industry_field}")
            if self._ip_field:
                logger.info(f"  IP field name: {self._ip_field}")
            if self._unit_field:
                logger.info(f"  Unit field name: {self._unit_field}")
            if self._industry_field:
                logger.info(f"  Industry field name: {self._industry_field}")
            
        except Exception as e:
            logger.error(f"Failed to check ip_info table: {e}")
            self._table_exists = False
            self._has_unit_field = False
            self._has_industry_field = False
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
    
    def _load_cache(self):
        """Load all IP-Unit-Industry mappings to memory"""
        if self._cache_loaded:
            return
        
        self._check_table_and_fields()
        
        if not self._table_exists:
            logger.warning("ip_info table does not exist, skipping cache load")
            self._cache_loaded = True
            return
        
        if not self._has_unit_field and not self._has_industry_field:
            logger.warning("ip_info table has no unit or industry fields, skipping cache load")
            self._cache_loaded = True
            return
        
        try:
            conn = pymysql.connect(**self.db_config)
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            # Build query
            select_fields = [f"`{self._ip_field}` as ip"]
            if self._has_unit_field:
                select_fields.append(f"`{self._unit_field}` as unit")
            if self._has_industry_field:
                select_fields.append(f"`{self._industry_field}` as industry")
            
            query = f"SELECT {', '.join(select_fields)} FROM ip_info"
            cursor.execute(query)
            
            results = cursor.fetchall()
            
            for row in results:
                unit = row.get('unit', '') if self._has_unit_field else ''
                industry = row.get('industry', '') if self._has_industry_field else ''
                
                # Only cache records with values
                if unit or industry:
                    self._cache[row['ip']] = (unit or None, industry or None)
            
            logger.info(f"IP-Unit-Industry mapping cache loaded: {len(self._cache)} records")
            self._cache_loaded = True
            
        except Exception as e:
            logger.error(f"Failed to load IP-Unit-Industry mapping cache: {e}")
            self._cache_loaded = True  # Mark as loaded to avoid retry
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
    
    def get_unit_industry(self, ip: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Get unit and industry for an IP
        
        Args:
            ip: IP address
            
        Returns:
            (unit, industry) tuple, returns (None, None) if not found
        """
        # Ensure cache is loaded
        self._load_cache()
        
        return self._cache.get(ip, (None, None))
    
    def get_unit(self, ip: str) -> Optional[str]:
        """Get unit for an IP"""
        unit, _ = self.get_unit_industry(ip)
        return unit
    
    def get_industry(self, ip: str) -> Optional[str]:
        """Get industry for an IP"""
        _, industry = self.get_unit_industry(ip)
        return industry
    
    def batch_get_unit_industry(self, ips: list) -> Dict[str, Tuple[Optional[str], Optional[str]]]:
        """
        Batch get unit and industry for IPs
        
        Args:
            ips: List of IP addresses
            
        Returns:
            {ip: (unit, industry)} dict
        """
        self._load_cache()
        
        return {ip: self._cache.get(ip, (None, None)) for ip in ips}
    
    def reload_cache(self):
        """Reload cache (call when ip_info table is updated)"""
        self._cache.clear()
        self._cache_loaded = False
        self._table_exists = None
        self._has_unit_field = None
        self._has_industry_field = None
        self._load_cache()
    
    def has_unit_field(self) -> bool:
        """Check if unit field exists"""
        self._check_table_and_fields()
        return self._has_unit_field
    
    def has_industry_field(self) -> bool:
        """Check if industry field exists"""
        self._check_table_and_fields()
        return self._has_industry_field


# Global singleton
_mapper_instance = None

def get_ip_unit_industry_mapper(db_config: Dict) -> IPUnitIndustryMapper:
    """Get global IP-Unit-Industry mapper instance"""
    global _mapper_instance
    if _mapper_instance is None:
        _mapper_instance = IPUnitIndustryMapper(db_config)
    return _mapper_instance
