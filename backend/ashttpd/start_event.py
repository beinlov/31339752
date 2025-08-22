from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
import hashlib, sys, os, threading, time, ssl, argparse, base64
import binascii
from urllib.parse import urlparse, parse_qs
import cgi

# 全局变量定义
flagExit = False  # 控制服务器是否退出的标志
flagTimeout = False  # 超时标志
serverTimeout = 0  # 服务器超时的延迟时间（单位：秒）

event_httpd = None  # HTTP 服务器对象
event_result = False  # 用于标记是否触发了特定请求


# 定义关闭 HTTP 服务器的函数，支持延迟关闭
def shutdownhttpd(server, delay):
    def handler(server, delay):
        global flagExit, flagTimeout
        if delay:  # 如果设置了延迟时间
            while delay > 0 and flagExit == False:
                time.sleep(1)
                delay -= 1
            if not flagExit:  # 如果没有手动关闭服务器，设置超时标志并关闭服务器
                flagTimeout = True
                print(" - TIMEOUT", file=sys.stderr)
        if flagExit:
            return  # 如果已经手动关闭服务器，跳过关闭操作
        flagExit = True  # 设置 flagExit 为 True，表示服务器要退出
        print(" - Shutting down httpd..", file=sys.stderr)
        server.shutdown()  # 关闭服务器

    # 启动一个线程来执行延迟关闭操作
    thr = threading.Thread(target=handler, args=(server, delay))
    thr.start()


# 超时关闭机制 (shutdownhttpd 函数)
# 功能: 在指定的延迟时间后关闭服务器。
# 主要逻辑:
# 启动一个后台线程，等待指定的延迟时间。
# 如果延迟时间到达且服务器未被手动关闭，则设置 flagTimeout 为 True 并关闭服务器。
# 如果服务器被手动关闭（如通过特定路径的请求），则直接返回。

# 定义处理 HTTP 请求的类
class ServerHandler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'  # HTTP 协议版本设置为 1.1

    # 设置 HTTP 响应头
    def _set_headers(self):
        self.send_response(200)  # 返回 HTTP 200 响应状态
        self.send_header('Content-Type', 'text/html')  # 设置响应内容类型为 HTML
        self.end_headers()  # 结束响应头

    # 处理 GET 请求
    def do_GET(self):
        global event_httpd, event_result
        print("GET REQUEST:", self.path)  # 打印接收到的 GET 请求路径

        # 如果请求路径是特定的值，则执行特定操作
        if self.path == '/225baaed270f6f9b97977a0db19f22f3' or self.path == '/cleanas/225baaed270f6f9b97977a0db19f22f3':
            message = b'72d89c8f2ba0111cc66a0bfcd027860c'  # 设置返回的消息（此处为一个固定的值）
            self.send_response(200)  # 返回 HTTP 200 响应状态
            self.send_header('Content-Type', 'text/html; charset=utf-8')  # 设置响应内容类型
            self.send_header('Content-Length', str(len(message)))  # 设置响应内容长度
            self.end_headers()  # 结束响应头
            self.wfile.write(message)  # 发送响应消息
            event_result = True  # 设置事件结果为 True，表示请求成功触发
            shutdownhttpd(event_httpd, delay=0)  # 关闭服务器
            return
        else:
            print("Unhandled: uri=" + self.path)  # 如果请求的路径不匹配，则打印信息

        message = b"NOT FOUND"  # 如果路径不匹配，返回 404 错误消息
        self.send_response(404)  # 返回 HTTP 404 响应状态
        self.send_header('Content-Length', str(len(message)))  # 设置响应内容长度
        self.end_headers()  # 结束响应头
        self.wfile.write(message)  # 发送 404 错误消息


# 功能: 继承自 BaseHTTPRequestHandler，用于处理 HTTP GET 请求。
# 主要逻辑:
# do_GET 方法:
# 检查请求的路径 (self.path)。如果路径是 /225baaed270f6f9b97977a0db19f22f3 或 /cleanas/225baaed270f6f9b97977a0db19f22f3，则返回一个固定的响应消息
# 72d89c8f2ba0111cc66a0bfcd027860c，并触发服务器关闭。
# 如果路径不匹配，则返回 404 NOT FOUND 响应。
# _set_headers 方法:
# 设置 HTTP 响应的状态码和头部信息。

# 定义支持多线程的 HTTP 服务器类
class MyHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True  # 设置守护线程，这样服务器关闭时，所有线程会被自动终止


# 功能: 继承自 ThreadingMixIn 和 HTTPServer，支持多线程处理 HTTP 请求。
# 特性: daemon_threads = True：确保服务器关闭时，所有线程也会被终止。

# 启动 HTTP 服务器的函数
def run(server_class=MyHTTPServer, handler_class=ServerHandler, port=80, enablessl=False):
    # server_class 指定了 HTTP 服务器的类型（类）。默认值是 MyHTTPServer，它是继承了 ThreadingMixIn 和 HTTPServer 的自定义服务器类
    # ServerHandler 是继承自 BaseHTTPRequestHandler 的自定义类，用来处理具体的 HTTP 请求。它定义了如何处理 GET 请求、POST 请求、以及其他 HTTP 方法。
    global flagExit, flagTimeout, event_httpd, event_result
    flagExit = False  # 初始化退出标志
    flagTimeout = False  # 初始化超时标志
    event_result = False  # 初始化事件结果标志

    server_address = ('', port)  # 设置服务器地址和端口
    httpd = server_class(server_address, handler_class)  # 创建 HTTP 服务器实例
    event_httpd = httpd  # 将服务器实例赋值给全局变量，用于在其他地方控制

    print(f' - Starting event_httpd(port={port})...', file=sys.stderr)  # 打印服务器启动信息

    # 启用 SSL 功能（如果 enablessl 为 True）
    if enablessl:
        pwd = os.path.dirname(os.path.realpath(__file__))  # 获取当前文件所在目录
        certfile = os.path.join(pwd, 'ssl.pem')  # SSL 证书文件路径
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)  # 创建 SSL 上下文对象
        context.load_cert_chain(certfile)  # 加载证书文件
        context.set_ciphers('DEFAULT:@SECLEVEL=0')  # 设置密码套件
        httpd.socket = context.wrap_socket(httpd.socket, server_side=True)  # 将 socket 包装为 SSL socket

    # 如果设置了超时时间，则启动后台线程在超时后关闭服务器
    if serverTimeout:
        shutdownhttpd(httpd, delay=serverTimeout)

    try:
        httpd.serve_forever()  # 启动服务器，持续监听请求
    except KeyboardInterrupt:
        print(' - Ctrl+C pressed...', file=sys.stderr)  # 捕获 Ctrl+C 结束运行
        shutdownhttpd(httpd, delay=0)  # 关闭服务器
    finally:
        httpd.server_close()  # 关闭服务器

    return event_result  # 返回事件结果，指示是否触发了特定路径的请求


# 服务器运行与关闭 (run 函数)
# 功能: 启动 HTTP 服务器，并支持 SSL 加密和超时关闭功能。
# 主要逻辑:
# 初始化服务器地址和端口。
# 如果启用 SSL (enablessl=True)，加载 SSL 证书并配置加密上下文。
# 如果设置了超时时间 (serverTimeout)，启动一个后台线程，在超时后关闭服务器。
# 使用 serve_forever 方法启动服务器，持续监听请求。
# 如果捕获到 KeyboardInterrupt（如按下 Ctrl+C），则关闭服务器。
# 返回 event_result，表示是否触发了特定路径的请求。

# 定义等待点击事件的函数
def wait_click_event():
    run(port=710)  # 启动 HTTP 服务器，监听端口 710
    return event_result  # 返回事件结果，表示是否收到了特定路径的请求


# 事件等待 (wait_click_event 函数)
# 功能: 启动 HTTP 服务器并等待特定路径的请求。
# 主要逻辑:
# 调用 run 函数启动服务器，监听端口 710。
# 返回 event_result，表示是否收到了特定路径的请求。

# 主程序执行部分
if __name__ == "__main__":
    if wait_click_event():  # 如果收到了特定路径的请求
        exit(0)  # 程序正常退出
    else:
        exit(3)  # 程序退出并返回错误代码 3

# 主程序逻辑
# 功能: 启动服务器并等待事件触发，根据事件结果退出程序。
# 主要逻辑:
# 调用 wait_click_event 函数，等待特定路径的请求。
# 如果收到请求（event_result 为 True），程序退出码为 0。
# 如果未收到请求或超时，程序退出码为 3。

# 这个代码实现了一个多线程 HTTP 服务器，主要功能是：
# 监听特定路径的 HTTP GET 请求（如 /225baaed270f6f9b97977a0db19f22f3）。
# 在收到特定路径的请求时，返回固定响应并关闭服务器。
# 支持 SSL 加密通信。
# 支持超时关闭机制。
# 通过退出码表示是否成功触发了特定事件。
# 这个服务器可以用于测试或作为某种事件触发的工具，例如等待外部请求后执行某些操作。
