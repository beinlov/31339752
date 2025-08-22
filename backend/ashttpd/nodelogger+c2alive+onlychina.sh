python3 httpd.py --logdir logdir --workmode stat --port 80 --c2verifyallowed --c2verifyallowed_chinaonly
#服务器以统计模式运行，记录访问日志到 logdir 目录。
#仅允许来自中国大陆的 IP 地址进行 C2 验证。
#适用于需要记录访问日志并限制验证范围的场景。