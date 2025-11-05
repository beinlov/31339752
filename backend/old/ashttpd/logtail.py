import hashlib, sys, os, threading, time, ssl, argparse
import binascii, time, json
from datetime import datetime, timedelta
import dbhlp_access, dbhlp_clean
import random
import start_event
from address_parse import is_ip_chinamainland
import glob


# Tail类：模拟Linux的tail命令，用于持续读取日志文件并处理每一行内容。
class Tail(object):
    ''' Represents a tail command. '''

    def __init__(self, tailed_file):
        ''' Initiate a Tail instance.
            Check for file validity, assigns callback function to standard out.

            Arguments:
                tailed_file - File to be followed. '''

        self.check_file_validity(tailed_file)  # 验证文件是否有效
        self.tailed_file = tailed_file  # 记录待跟踪的文件路径
        self.callback = sys.stdout.write  # 默认的回调函数是写入标准输出
        self.timer1s = None  # 定时器，每秒执行的回调函数

    # Tail类用于跟踪日志文件的变化，类似于Unix的tail -f命令。它会持续读取日志文件的新内容，并将新行传递给回调函数进行处理。
    # 主要方法:
    # __init__: 初始化Tail实例，检查文件的有效性（是否存在、是否可读、是否是文件）。
    # follow: 持续跟踪文件的新内容，每隔一段时间检查文件是否有新行，如果有则调用回调函数处理。
    # register_callback: 允许用户注册自定义的回调函数，用于处理每一行日志。

    #代码实现了持续监控一个文件的变化，并在文件有新的行时触发相应的操作。
    def follow(self, s=1, old=False):
        ''' Do a tail follow. If a callback function is registered it is called with every new line.
        Else printed to standard out.

        Arguments:
            s - Number of seconds to wait between each iteration; Defaults to 1. '''

        with open(self.tailed_file, "rb") as file_:
            # Go to the end of file
            if not old:
                file_.seek(0, os.SEEK_END)  # 定位到文件末尾
            ts_last = 0
            while True:
                curr_position = file_.tell()  # 获取当前文件位置
                line = file_.readline()  # 读取一行
                if not line:  # 如果没有新行
                    file_.seek(curr_position)  # 继续保持当前位置
                    time.sleep(s)  # 等待指定的时间
                else:
                    self.callback(line)  # 调用回调函数处理新行
                if self.timer1s is not None:  # 如果定义了每秒调用的定时器
                    if time.time() - ts_last >= 1:  # 每秒检查一次
                        if not self.timer1s():  # 如果定时器返回False，结束跟踪
                            break
                        ts_last = time.time()

    def register_callback(self, func, timer1s=None):
        ''' Overrides default callback function to provided function. '''
        self.callback = func  # 注册新地回调函数
        self.timer1s = timer1s  # 注册定时器函数

    def check_file_validity(self, file_):
        ''' Check whether the given file exists, readable and is a file '''
        if not os.access(file_, os.F_OK):
            raise TailError("File '%s' does not exist" % (file_))  # 检查文件是否存在
        if not os.access(file_, os.R_OK):
            raise TailError("File '%s' not readable" % (file_))  # 检查文件是否可读
        if os.path.isdir(file_):
            raise TailError("File '%s' is a directory" % (file_))  # 检查是否是文件而非目录


# 定义TailError异常类
class TailError(Exception):
    def __init__(self, msg):
        self.message = msg  # 错误消息

    def __str__(self):
        return self.message  # 返回错误消息


# 格式化时间差为字符串
def format_timedelta(td):
    total_seconds = int(td.total_seconds())  # 获取总秒数
    hours = total_seconds // 3600  # 计算小时数
    minutes = (total_seconds % 3600) // 60  # 计算分钟数
    if hours > 0 and minutes > 0:
        return f"{hours}小时{minutes}分钟"
    elif hours > 0:
        return f"{hours}小时"
    elif minutes > 0:
        return f"{minutes}分钟"
    else:
        return "0分钟"
# 将时间差格式化为易于阅读的字符串（如 "2小时30分钟"）。
# 从指定文件中读取每一行并加入到列表中
def lines_from_file(filename, outls):
    # 打开文件，并使用 UTF-8 编码读取内容
    with open(filename, "r", encoding='utf-8') as _f:
        # 逐行读取文件
        for line in _f:
            line = line.strip()  # 去除每行末尾的空白字符
            if line:  # 如果行非空，则添加到输出列表中
                outls.append(line)

# 用于在字典 d 中记录特定键 x 的出现次数
def countd(d, x):
    t = d.get(x)  # 获取字典中键 x 的值
    if t is None:  # 如果键 x 不存在
        d[x] = 1  # 添加键 x，初始值为 1
    else:
        d[x] += 1  # 如果键 x 存在，增加其值

# 设置和记录的全局变量
set_last_line_number = 0  # 设置最后行号的标记
last_line_number = 0  # 上次处理的行号

# 数据库更新间隔配置（以秒为单位）
db_update_interval_access = 60  # 更新访问日志的间隔
db_last_update_access = 0  # 上次更新访问日志的时间
db_update_interval_clean = 10  # 更新清理日志的间隔
db_last_update_clean = 0  # 上次更新清理日志的时间

# 存储批量记录的列表（访问日志和清理日志）
db_recbunch_access = []  # 存储访问日志
db_recbunch_clean = []  # 存储清理日志

# 存储已处理过的 IP 地址历史集合（避免重复处理相同 IP）
accesslog_ip_history = set()

# 处理每一行日志数据的回调函数
def on_newline(line):
    global last_line_number, db_last_update
    line = line.decode("utf-8")  # 解码为 UTF-8 编码的字符串
    parts = line.strip().split(',')  # 按逗号分割每行日志为多个字段
    if len(parts) < 3:  # 如果字段数目小于 3，则说明格式错误，跳过该行
        print(" - field count incorrect.", file=sys.stderr)
        return

    last_line_number += 1  # 记录处理的行号
    if set_last_line_number and last_line_number < set_last_line_number:
        return  # 如果设置了最后处理的行号，则跳过之前的行

    # 获取日志中的时间戳、IP 地址和模式字段
    datetime_str = parts[0]
    strIP = parts[1]
    strMode = parts[2]
    print("%d.    %s    %s    %s" % (last_line_number, datetime_str, strIP, strMode))

    # 生成每日的 IP 字符串（用于检查 IP 是否为同一 IP 地址）
    strIPDaily = datetime_str[:10] + strIP
    is_new_ip = False

    # 如果该 IP 地址的日期记录未出现过，则标记为新 IP
    if not strIPDaily in accesslog_ip_history:
        is_new_ip = True
        accesslog_ip_history.add(strIPDaily)  # 将其加入历史记录

    # 处理访问日志
    if strMode == 'access':
        if is_new_ip:
            # 如果是新 IP 地址，将其记录到 db_recbunch_access 中
            db_recbunch_access.append({'ts': datetime_str, 'ip': strIP})
    # 处理特定的清理命令（如 'qla0'）
    elif strMode == 'qla0' and len(parts) > 3:
        # 使用 IP 和 UUID 生成唯一标识符，用于避免重复记录相同的 IP 和 UUID
        strUUIDDayly = strIPDaily + parts[3]
        if not strUUIDDayly in accesslog_ip_history:
            accesslog_ip_history.add(strUUIDDayly)
            db_recbunch_access.append({'ts': datetime_str, 'ip': strIP, 'uuid': parts[3]})
    # 处理清理操作的日志（如 'clean0', 'clean1', 'cleanw1'）
    elif strMode in ['clean0', 'clean1', 'cleanw1']:
        # 将清理日志添加到 db_recbunch_clean 中
        db_recbunch_clean.append({'ts': datetime_str, 'ip': strIP})

# 功能: 这是 Tail 类的回调函数，用于处理每一行日志。它会解析日志行，提取时间戳、IP 地址和模式（如 access、clean0 等），并根据模式将数据存储到不同的数据库记录集中。
# 主要逻辑:
# 解析日志行，提取时间戳、IP 地址和模式。
# 根据模式（如 access、clean0 等）将数据存储到 db_recbunch_access 或 db_recbunch_clean 列表中。
# 如果是新的 IP 地址，则将其添加到 accesslog_ip_history 集合中。
# 定时器回调函数，每秒执行一次，用于处理访问日志和清理日志的数据库插入操作
def on_timer_1s(chkdatetime = True, forceflush=False):
    global last_line_number, db_last_update_clean, db_last_update_access, db_recbunch_clean, db_recbunch_access
    # 检查日期是否变更，如果变更则不进行插入操作
    if chkdatetime:
        if day_time != time.strftime('%Y-%m-%d', time.localtime()):  # 判断当前日期是否与上次处理日期不同
            return False  # 如果日期发生变化，返回 False，跳过当前处理

    now = datetime.now()  # 获取当前时间
    # 如果需要强制刷新或距离上次访问日志更新的时间超过了设定的更新间隔
    if forceflush or time.time() - db_last_update_access >= db_update_interval_access:
        if db_recbunch_access:  # 如果访问日志队列不为空
            print(f" * {str(now)}   db inserting accesslog(count={len(db_recbunch_access)})....")  # 输出日志
            try:
                dbhlp_access.add(db_recbunch_access)  # 插入访问日志到数据库
                dbhlp_access.add_uuid(db_recbunch_access)  # 插入访问日志的 UUID 数据
                db_recbunch_access.clear()  # 清空访问日志队列
                db_last_update_access = time.time()  # 更新访问日志的最后更新时间
            except Exception as e:  # 异常处理
                print("exception: db: " + str(e))  # 打印异常信息
        else:
            db_last_update_access = time.time()  # 如果队列为空，仅更新访问日志的最后更新时间

    # 如果需要强制刷新或距离上次清理日志更新的时间超过了设定的更新间隔
    if forceflush or time.time() - db_last_update_clean >= db_update_interval_clean:
        if db_recbunch_clean:  # 如果清理日志队列不为空
            print(f" * {str(now)}   db inserting cleanlog(count={len(db_recbunch_clean)})....")  # 输出日志
            try:
                dbhlp_clean.add(db_recbunch_clean)  # 插入清理日志到数据库
                db_recbunch_clean.clear()  # 清空清理日志队列
                db_last_update_clean = time.time()  # 更新清理日志的最后更新时间
            except Exception as e:  # 异常处理
                print("exception: db: " + str(e))  # 打印异常信息
        else:
            db_last_update_clean = time.time()  # 如果队列为空，仅更新清理日志的最后更新时间

    return True  # 返回 True，表示处理完成

# 定时器回调函数，用于将访问日志的 UUID 数据推送到数据库
def on_timer_push_uuids(chkdatetime = False, forceflush=False):
    global db_last_update_access, db_recbunch_access

    now = datetime.now()  # 获取当前时间
    # 如果需要强制刷新、访问日志队列数据量达到 1000，或者距离上次访问日志更新的时间超过了设定的更新间隔
    if forceflush or len(db_recbunch_access) >= 1000 or time.time() - db_last_update_access >= db_update_interval_access:
        print(f" * {str(now)}   db inserting nodes(count={len(db_recbunch_access)})....")  # 输出日志
        try:
            dbhlp_access.add_uuid(db_recbunch_access)  # 将访问日志的 UUID 数据插入到数据库
            db_recbunch_access.clear()  # 清空访问日志队列
            db_last_update_access = time.time()  # 更新访问日志的最后更新时间
        except Exception as e:  # 异常处理
            print("exception: db: " + str(e))  # 打印异常信息
    else:
        db_last_update_access = time.time()  # 如果没有达到插入条件，仅更新时间

    return True  # 返回 True，表示处理完成

# 功能: 这些函数用于定时将 db_recbunch_access 和 db_recbunch_clean 中的数据批量插入到数据库中。
# 主要逻辑:
# on_timer_1s: 每隔一定时间（如 60 秒）将 db_recbunch_access 和 db_recbunch_clean 中的数据插入到数据库中。
# on_timer_push_uuids: 专门用于处理 UUID 相关的数据，每隔一定时间或数据量达到一定阈值时，将数据插入到数据库中。
# 获取指定目录下符合格式要求的所有文件
def get_files_with_format(directory, format="????-??-??.txt"):
    # 使用 glob 模块构建一个匹配指定格式的文件路径模式
    file_pattern = os.path.join(directory, format)
    # 使用 glob 函数找到所有匹配该模式的文件
    file_list = glob.glob(file_pattern)
    return file_list  # 返回所有匹配的文件列表

# 处理历史日志文件，将每个文件中的每一行传递给处理函数进行处理
def push_history(files, handler):
    # 遍历所有历史日志文件
    for file in files:
        print("parsing " + file)  # 打印正在解析的文件名称
        with open(file, "rb") as file_:  # 打开文件以二进制模式读取
            ts_last = 0  # 用于记录上次处理的时间戳（目前未使用）
            # 持续读取文件中的每一行
            while True:
                line = file_.readline()  # 读取一行
                if not line:  # 如果没有读取到新行，说明文件已读完
                    break  # 退出循环
                on_newline(line)  # 将读取到的行传递给 on_newline 函数进行处理
                handler(chkdatetime=False)  # 调用处理函数，传递 `chkdatetime=False` 参数
    # 完成所有文件处理后，强制刷新缓存
    handler(chkdatetime=False, forceflush=True)
    # 功能: 用于处理历史日志文件，将历史日志数据推送到数据库中。
    # 主要逻辑:
    # 遍历指定目录下的所有历史日志文件，逐行读取并调用on_newline函数处理。
    # 处理完成后，调用on_timer_1s或on_timer_push_uuids函数将数据插入到数据库中。

if __name__ == "__main__":  # 仅在脚本作为主程序运行时执行以下代码
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description='')  # 初始化 ArgumentParser 对象
    parser.add_argument('--logdir', action='store', help='', dest='logdir', default='')  # 日志目录参数
    parser.add_argument('--lastlinenumber', action='store', help='', dest='lastlinenumber')  # 设置读取的起始行号
    parser.add_argument('--old', action='store_true', help='', dest='old', default=False)  # 是否读取历史日志（默认值为 False）
    parser.add_argument('--test', action='store', help='', dest='test')  # 测试文件路径参数
    parser.add_argument('--testtype2', action='store_true', help='', dest='testtype2', default=False)  # 测试类型2标志
    parser.add_argument('--rightnow', action='store_true', help='', dest='rightnow', default=False)  # 立即执行标志
    parser.add_argument('--testbutton', action='store_true', help='', dest='testbutton', default=False)  # 测试按钮标志
    parser.add_argument('--cleanglobal', action='store_true', help='', dest='cleanglobal', default=False)  # 是否清理全球数据
    parser.add_argument('--pushhistory', action='store_true', help='', dest='pushhistory', default=False)  # 是否推送历史数据
    parser.add_argument('--pushhistoryuuid', action='store_true', help='', dest='pushhistoryuuid', default=False)  # 是否推送包含 UUID 的历史数据

    args = parser.parse_args()  # 解析命令行参数

    # 设置起始读取的行号
    if args.lastlinenumber:
        set_last_line_number = int(args.lastlinenumber)

    # 如果有指定测试文件，则执行测试流程
    if args.test:
        # 如果 rightnow 参数没有指定，则等待某个事件发生（点击等）
        if not args.rightnow:
            if not start_event.wait_click_event():
                print("bug??")  # 如果事件没有发生，则打印错误信息
                exit(3)  # 退出程序并返回错误码 3

        # 如果 testbutton 参数被指定，则持续等待点击事件并执行
        if args.testbutton:
            while True:
                if not start_event.wait_click_event():  # 等待点击事件
                    print("bug??")  # 如果事件没有发生，则打印错误信息
                    exit(3)  # 退出程序并返回错误码 3
                print("GOOD")  # 事件触发时打印 "GOOD"

        # 打开测试文件并逐行读取进行处理
        with open(args.test, "rb") as _f:
            number = 0  # 行号计数
            pushed = set()  # 用于记录已处理的 IP 地址，避免重复处理
            for line in _f:  # 遍历每一行
                number += 1  # 行号递增
                if number < set_last_line_number:  # 如果当前行号小于设置的起始行号，则跳过该行
                    continue
                line = line.decode("gb2312")  # 将行数据从 GB2312 编码解码为字符串
                if args.testtype2:  # 如果是第二种测试类型
                    parts = line.strip().split(' | ')  # 以 ' | ' 分割行
                    ip = parts[0]  # 获取 IP 地址
                else:
                    parts = line.strip().split(',')  # 以 ',' 分割行
                    ip = parts[1]  # 获取 IP 地址
                if ip in pushed or not ip:  # 如果 IP 地址已经处理过，或 IP 地址为空，则跳过该行
                    continue
                # 如果 cleanglobal 参数为 False 且 IP 地址不属于中国大陆，则跳过该行
                if not args.cleanglobal:
                    if not is_ip_chinamainland(ip):
                        continue
                pushed.add(ip)  # 将处理过的 IP 地址添加到 pushed 集合中
                # 将处理结果添加到 db_recbunch_clean 中
                db_recbunch_clean.append({'ts': str(datetime.now())[:19], 'ip': ip})
                # 如果 db_recbunch_clean 中的数据达到 100 条，则插入数据库并清空队列
                if len(db_recbunch_clean) >= 100:
                    print(f"line number = {number}")
                    dbhlp_clean.add(db_recbunch_clean)  # 将数据插入数据库
                    db_recbunch_clean.clear()  # 清空队列
                    time.sleep(1)  # 延迟 1 秒
            # 如果还有剩余数据，则插入数据库
            if db_recbunch_clean:
                dbhlp_clean.add(db_recbunch_clean)
                db_recbunch_clean.clear()

    # 如果指定了 pushhistory 参数，则处理历史日志文件并推送数据
    elif args.pushhistory:
        files = get_files_with_format(args.logdir)  # 获取日志目录下符合格式的文件
        push_history(files, on_timer_1s)  # 推送历史文件并处理每一行

    # 如果指定了 pushhistoryuuid 参数，则处理历史日志文件并推送包含 UUID 的数据
    elif args.pushhistoryuuid:
        files = get_files_with_format(args.logdir)  # 获取日志目录下符合格式的文件
        push_history(files, on_timer_push_uuids)  # 推送历史文件并处理每一行（包括 UUID）

    # 否则进入主循环，实时跟踪日志文件的变化
    else:
        while True:
            day_time = time.strftime('%Y-%m-%d', time.localtime())  # 获取当前日期
            logfile = os.path.join(args.logdir, day_time + '.txt')  # 构造日志文件路径
            accesslog_ip_history.clear()  # 清空访问日志 IP 地址历史记录
            try:
                print("Tail following " + logfile)  # 打印正在跟踪的日志文件
                tailf = Tail(logfile)  # 创建 Tail 对象，实时跟踪文件
                tailf.register_callback(on_newline, on_timer_1s)  # 注册回调函数
                tailf.follow(s=0.5, old=args.old)  # 开始实时跟踪文件内容
            except KeyboardInterrupt:
                print("Ctrl+C Pressed.")  # 捕获到 Ctrl+C 时，退出程序
                break
            except Exception as e:
                # 捕获异常并打印出错信息
                print(f"发生异常：{e}")
            time.sleep(1)  # 每次循环后延迟 1 秒

            # 功能: 通过命令行参数控制程序的行为，如指定日志目录、设置起始行号、处理历史数据等。
            # 主要参数:
            # --logdir: 指定日志文件所在的目录。
            # --lastlinenumber: 设置起始行号，从指定行号开始处理日志。
            # --pushhistory: 处理历史日志文件。
            # --pushhistoryuuid: 处理历史日志文件中的UUID数据。
            # --test: 测试模式，用于测试日志文件的处理逻辑。

# 这个代码主要用于实时监控日志文件的变化，并将日志数据存储到数据库中。它支持处理历史日志文件，并且可以通过命令行参数灵活控制程序的行为。代码中还包含了一些辅助功能，如 IP 地址检查、时间格式化等。