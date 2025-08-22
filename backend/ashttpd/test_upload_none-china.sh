mkdir store-nonechina-only
python3 httpd.py --logdir logdir --workmode file --datadir store-nonechina-only --port 80 --allowip allow-allips.txt
#服务器以文件模式运行，处理文件上传请求。
#上传的文件存储到 store-nonechina-only 目录。
#仅允许 allow-allips.txt 文件中列出的 IP 地址访问服务器。
#适用于需要限制访问 IP 并处理文件上传的场景。