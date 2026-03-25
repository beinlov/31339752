# -*- coding: utf-8 -*-
import pandas as pd

def classify_industry(unit):
    if pd.isna(unit) or unit == '*' or unit == '':
        return 'qita'
    
    unit_str = str(unit).strip()
    
    # University keywords
    if any(k in unit_str for k in ['大学', '学院', '高校', '师范', '理工', '科技大学']):
        return 'zhongdiangaoxiao'
    
    # Hospital keywords
    if any(k in unit_str for k in ['医院', '卫生院', '诊所', '医疗', '中医', '妇幼']):
        return 'yiyuan'
    
    # Research keywords
    if any(k in unit_str for k in ['研究院', '研究所', '研究中心', '科学院', '实验室', '技术中心']):
        return 'keyansuosuo'
    
    # Government keywords
    if any(k in unit_str for k in ['政府', '人民政府', '市委', '省委', '党委', '法院', '检察院', '公安', '财政', '税务']):
        return 'dangzhengj iguan'
    
    # Company keywords
    if any(k in unit_str for k in ['公司', '有限责任', '股份', '集团', '企业', '科技', '网络', '腾讯', '阿里']):
        return 'gongsi'
    
    return 'qita'

# Map back to Chinese
industry_map = {
    'zhongdiangaoxiao': '重点高校',
    'dangzhengj iguan': '党政机关',
    'keyansuosuo': '科研院所',
    'yiyuan': '医院',
    'gongsi': '公司',
    'qita': '其他'
}

file_path = r'd:\dell\Desktop\botnet\20260321汇总IP归属（114+国口）发哈工大.xlsx'
df = pd.read_excel(file_path)

print(f'Total rows: {len(df)}')
print('\nOriginal industry:')
print(df['industry'].value_counts())

df['industry'] = df['unit'].apply(classify_industry).map(industry_map)

print('\nNew industry:')
print(df['industry'].value_counts())

output_path = r'd:\dell\Desktop\botnet\20260321汇总IP归属（114+国口）发哈工大_分类后.xlsx'
df.to_excel(output_path, index=False)
print(f'\nSaved to: {output_path}')
