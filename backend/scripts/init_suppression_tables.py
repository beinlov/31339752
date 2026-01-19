"""
��ʼ��������Ϲ�����������ݿ��
���д˽ű��Դ���IP���������������������������Ե���ر�
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config import DB_CONFIG
import pymysql

def init_suppression_tables():
    """��ʼ�����������ر�"""
    print("=" * 60)
    print("��ʼ��������Ϲ������ݿ��")
    print("=" * 60)
    print(f"���ݿ�: {DB_CONFIG['host']}/{DB_CONFIG['database']}")
    print("=" * 60)
    
    conn = pymysql.connect(
        host=DB_CONFIG['host'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        database=DB_CONFIG['database'],
        charset='utf8mb4'
    )
    
    try:
        cursor = conn.cursor()
        
        print("\n���� 1/5: ���� IP��������...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ip_blacklist (
                id INT AUTO_INCREMENT PRIMARY KEY,
                ip_address VARCHAR(45) UNIQUE NOT NULL COMMENT 'IP��ַ',
                description VARCHAR(200) COMMENT '������Ϣ',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '����ʱ��',
                INDEX idx_ip (ip_address),
                INDEX idx_created_at (created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='IP��������'
        """)
        print("? IP������������ɹ�")
        
        print("\n���� 2/5: ���� ������������...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS domain_blacklist (
                id INT AUTO_INCREMENT PRIMARY KEY,
                domain VARCHAR(255) UNIQUE NOT NULL COMMENT '����',
                description VARCHAR(200) COMMENT '������Ϣ',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '����ʱ��',
                INDEX idx_domain (domain),
                INDEX idx_created_at (created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='������������'
        """)
        print("? ����������������ɹ�")
        
        print("\n���� 3/5: ���� �������Ա�...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS packet_loss_policy (
                id INT AUTO_INCREMENT PRIMARY KEY,
                ip_address VARCHAR(45) UNIQUE NOT NULL COMMENT 'Ŀ��IP��ַ',
                loss_rate FLOAT NOT NULL COMMENT '������(0.0-1.0)',
                description VARCHAR(200) COMMENT '������Ϣ',
                enabled BOOLEAN DEFAULT TRUE COMMENT '�Ƿ�����',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '����ʱ��',
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '����ʱ��',
                INDEX idx_ip (ip_address),
                INDEX idx_enabled (enabled),
                INDEX idx_created_at (created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='��Ъ�Զ������Ա�'
        """)
        print("? �������Ա�����ɹ�")
        
        print("\n���� 4/5: ���� �˿���Դ���������...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS port_consume_task (
                id INT AUTO_INCREMENT PRIMARY KEY,
                task_id VARCHAR(100) UNIQUE NOT NULL COMMENT '����ΨһID',
                target_ip VARCHAR(45) NOT NULL COMMENT 'Ŀ��IP��ַ',
                target_port INT NOT NULL COMMENT 'Ŀ��˿�',
                threads INT DEFAULT 100 COMMENT '�߳���',
                status VARCHAR(20) DEFAULT 'running' COMMENT '����״̬: running, stopped, error',
                start_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '���ʱ��',
                stop_time DATETIME COMMENT 'ֹͣʱ��',
                INDEX idx_task_id (task_id),
                INDEX idx_status (status),
                INDEX idx_start_time (start_time)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='�˿���Դ���������'
        """)
        print("? �˿���Դ�������������ɹ�")
        
        print("\n���� 5/5: ���� SYN��ˮ���������...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS syn_flood_task (
                id INT AUTO_INCREMENT PRIMARY KEY,
                task_id VARCHAR(100) UNIQUE NOT NULL COMMENT '����ΨһID',
                target_ip VARCHAR(45) NOT NULL COMMENT 'Ŀ��IP��ַ',
                target_port INT NOT NULL COMMENT 'Ŀ��˿�',
                threads INT DEFAULT 50 COMMENT '�߳���',
                duration INT COMMENT '����ʱ��(��)',
                rate INT COMMENT '����(��/��)',
                status VARCHAR(20) DEFAULT 'running' COMMENT '����״̬: running, stopped, error',
                start_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '���ʱ��',
                stop_time DATETIME COMMENT 'ֹͣʱ��',
                INDEX idx_task_id (task_id),
                INDEX idx_status (status),
                INDEX idx_start_time (start_time)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='SYN��ˮ���������'
        """)
        print("? SYN��ˮ�������������ɹ�")
        
        conn.commit()
        
        print("\n" + "=" * 60)
        print("? ���б������ɣ�")
        print("=" * 60)
        
        # �鿴�����ı�
        print("\n��ǰ���ݿ��е����������ر�:")
        cursor.execute("""
            SELECT table_name, table_comment 
            FROM information_schema.TABLES 
            WHERE table_schema = %s 
            AND table_name IN ('ip_blacklist', 'domain_blacklist', 'packet_loss_policy', 
                               'port_consume_task', 'syn_flood_task')
        """, (DB_CONFIG['database'],))
        
        tables = cursor.fetchall()
        for table in tables:
            print(f"  - {table[0]}: {table[1]}")
        
        print("\n" + "=" * 60)
        print("���ݿ��ʼ����ɣ�")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n? ����: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()
    
    return True


if __name__ == "__main__":
    try:
        success = init_suppression_tables()
        if success:
            print("\n? �ű�ִ�гɹ�")
            sys.exit(0)
        else:
            print("\n? �ű�ִ��ʧ��")
            sys.exit(1)
    except Exception as e:
        print(f"\n? �ű�ִ�г���: {e}")
        sys.exit(1)
