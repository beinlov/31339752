# -*- coding: utf-8 -*-
"""
修复文件编码问题的脚本
将 GBK 误编码的中文恢复为正确的 UTF-8
"""
import os

def fix_file_encoding(filepath):
    """修复单个文件的编码"""
    try:
        # 尝试以 latin-1 读取（保留原始字节）
        with open(filepath, 'r', encoding='latin-1') as f:
            content = f.read()
        
        # 将错误编码的字符串转换回字节，然后用 GBK 解码
        try:
            # 尝试将 latin-1 字符转回字节，再用 GBK 解码
            fixed_content = content.encode('latin-1').decode('gbk')
            
            # 写回文件（UTF-8编码）
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            
            print(f"✅ 已修复: {filepath}")
            return True
        except (UnicodeDecodeError, UnicodeEncodeError):
            print(f"⚠️  跳过（无需修复）: {filepath}")
            return False
            
    except Exception as e:
        print(f"❌ 错误: {filepath} - {e}")
        return False

# 修复指定文件
files_to_fix = [
    'router/suppression_config_push.py',
    'router/sybil_attack_test.py'
]

print("开始修复文件编码...\n")
for file in files_to_fix:
    filepath = os.path.join(os.path.dirname(__file__), file)
    if os.path.exists(filepath):
        fix_file_encoding(filepath)
    else:
        print(f"❌ 文件不存在: {filepath}")

print("\n修复完成！")
