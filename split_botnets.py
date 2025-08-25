import mysql.connector
from mysql.connector import Error

def create_connection():
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='Zm.1575098153',  # 请替换为你的数据库密码
            database='botnet'
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL Database: {e}")
        return None

def create_botnet_tables(connection):
    try:
        cursor = connection.cursor()
        
        # 创建各个全球僵尸网络表
        botnet_types = ['mozi', 'asruex', 'andromeda', 'leethozer', 'moobot']
        
        for botnet_type in botnet_types:
            table_name = f"global_botnet_{botnet_type}"
            cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id INT AUTO_INCREMENT PRIMARY KEY,
                country VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
                infected_num INT(11) NULL DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY idx_country (country),
                INDEX idx_infected_num (infected_num)
            ) ENGINE = MyISAM CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic
            """)

        # 创建全球僵尸网络汇总表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS global_botnets (
            id INT AUTO_INCREMENT PRIMARY KEY,
            country VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
            botnet_type VARCHAR(50) NOT NULL,
            infected_num INT(11) NULL DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY idx_country_botnet (country, botnet_type),
            INDEX idx_botnet_type (botnet_type)
        ) ENGINE = MyISAM CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic
        """)
        
        connection.commit()
        print("Tables created successfully")
        
    except Error as e:
        print(f"Error creating tables: {e}")

def split_data(connection):
    try:
        cursor = connection.cursor()
        
        # 获取所有僵尸网络类型
        botnet_types = ['mozi', 'asruex', 'andromeda', 'leethozer', 'moobot']
        
        for botnet_type in botnet_types:
            # 从global_botnets表中获取特定类型的数据
            cursor.execute("""
                SELECT country, infected_num 
                FROM global_botnets 
                WHERE botnet_type = %s
            """, (botnet_type,))
            
            records = cursor.fetchall()
            
            if records:
                # 准备批量插入数据
                table_name = f"global_botnet_{botnet_type}"
                insert_query = f"""
                    INSERT INTO {table_name} (country, infected_num)
                    VALUES (%s, %s)
                    ON DUPLICATE KEY UPDATE
                    infected_num = VALUES(infected_num),
                    updated_at = CURRENT_TIMESTAMP
                """
                
                # 批量插入数据
                cursor.executemany(insert_query, records)
                print(f"Inserted {len(records)} records into {table_name}")
        
        connection.commit()
        print("Data split successfully")
        
    except Error as e:
        print(f"Error splitting data: {e}")
        connection.rollback()

def main():
    connection = create_connection()
    if connection is not None:
        try:
            # 创建所有需要的表
            create_botnet_tables(connection)
            
            # 分割数据到各个表中
            split_data(connection)
            
            print("All operations completed successfully")
        except Error as e:
            print(f"Error in main: {e}")
        finally:
            connection.close()
    else:
        print("Failed to create database connection")

if __name__ == "__main__":
    main() 