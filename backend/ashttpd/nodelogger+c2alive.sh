python3 httpd.py --logdir logdir --workmode stat --port 80 --c2verifyallowed
#服务器以统计模式运行，记录访问日志到 logdir 目录。
#允许所有 IP 地址进行 C2 验证。
#适用于需要记录访问日志并允许全局验证的场景。