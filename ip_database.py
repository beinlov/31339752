import pandas as pd
from sqlalchemy import create_engine, MetaData, Table, Column, String, Integer, inspect
import pymysql

# ===== 配置 =====
EXCEL_FILE1 = "归属IP.xlsx"                               # 第一个 Excel 文件
EXCEL_FILE2 = "20260316归属IP所属领域-发哈工大&测评中心.xlsx"  # 第二个 Excel 文件
MYSQL_HOST = "localhost"
MYSQL_PORT = 3306
MYSQL_USER = "root"
MYSQL_PASSWORD = "Matrix123"
MYSQL_DATABASE = "botnet"
TABLE_NAME = "ip_info"

# ===== 连接 MySQL =====
engine = create_engine(f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?charset=utf8mb4")

# ===== 删除旧表（如需重建） =====
# 警告：这会删除表中所有已有数据，请确认！
inspector = inspect(engine)
if inspector.has_table(TABLE_NAME):
    print(f"表 {TABLE_NAME} 已存在，正在删除...")
    Table(TABLE_NAME, MetaData(), autoload_with=engine).drop(engine)

# ===== 创建新表（仅包含所需三列 + id） =====
metadata = MetaData()
columns = [
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('IP', String(50), nullable=True),        # IP 地址长度可能 15-45
    Column('单位', String(255), nullable=True),
    Column('应用场景', String(100), nullable=True)
]
table = Table(TABLE_NAME, metadata, *columns)
metadata.create_all(engine)
print(f"表 {TABLE_NAME} 创建成功（字段：IP, 单位, 应用场景）")

# ===== 读取第一个文件：Sheet1 中“家庭宽带”数据 =====
print("正在处理归属IP.xlsx...")
df1 = pd.read_excel(EXCEL_FILE1, sheet_name="Sheet1")
# 筛选“应用场景”为“家庭宽带”
df1_filtered = df1[df1["应用场景"] == "家庭宽带"].copy()
# 只保留所需三列
df1_result = df1_filtered[["IP", "单位", "应用场景"]]
print(f"从归属IP.xlsx 筛选出 {len(df1_result)} 条家庭宽带记录")

# ===== 读取第二个文件：所有 sheet，将 sheet 名作为应用场景 =====
print("正在处理第二个文件...")
xls2 = pd.ExcelFile(EXCEL_FILE2)
sheet_names = xls2.sheet_names
df2_list = []

for sheet in sheet_names:
    print(f"  处理工作表：{sheet}")
    df_sheet = pd.read_excel(xls2, sheet_name=sheet)

    # 尝试获取 IP 和单位列（假设列名为 'IP' 和 '单位'，否则用前两列）
    ip_col = None
    unit_col = None
    # 先查找标准列名（不区分大小写）
    for col in df_sheet.columns:
        if col.lower() in ['ip', 'ip地址', '受害地址']:   # 常见 IP 列名
            ip_col = col
        if col.lower() in ['单位', '归属1', '归属']:
            unit_col = col

    # 如果未找到，则默认使用第一列作为 IP，第二列作为单位（根据常见格式）
    if ip_col is None:
        ip_col = df_sheet.columns[0]
        print(f"    未找到IP列，使用第一列 '{ip_col}' 作为IP")
    if unit_col is None:
        unit_col = df_sheet.columns[1] if len(df_sheet.columns) > 1 else None
        if unit_col:
            print(f"    未找到单位列，使用第二列 '{unit_col}' 作为单位")
        else:
            print(f"    警告：工作表 {sheet} 只有一列，无法提取单位，将留空")

    temp_df = df_sheet[[ip_col, unit_col]].copy() if unit_col else df_sheet[[ip_col]].copy()
    temp_df.columns = ["IP", "单位"] if unit_col else ["IP"]
    if not unit_col:
        temp_df["单位"] = None

    temp_df["应用场景"] = sheet
    df2_list.append(temp_df)

df2_result = pd.concat(df2_list, ignore_index=True)
print(f"从第二个文件共提取 {len(df2_result)} 条记录")

# ===== 合并两个 DataFrame =====
final_df = pd.concat([df1_result, df2_result], ignore_index=True)

# 去除可能的空值行（如果IP为空则丢弃）
final_df = final_df.dropna(subset=["IP"])

print(f"合并后总记录数：{len(final_df)}")

# ===== 写入 MySQL =====
with engine.connect() as conn:
    final_df.to_sql(TABLE_NAME, conn, if_exists="append", index=False, method='multi')
    print("数据写入完成！")