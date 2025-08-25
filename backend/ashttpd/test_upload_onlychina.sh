mkdir store-china-only
python3 httpd.py --logdir logdir --workmode file --datadir store-china-only --port 80 --onlychinafile --allowip allow-allips.txt
#服务器以文件模式运行，处理文件上传请求。
#上传的文件存储到 store-china-only 目录。
#仅允许来自中国大陆的 IP 地址上传文件，并且仅允许 allow-allips.txt 文件中列出的 IP 地址访问服务器。
#适用于需要限制访问 IP 并仅允许中国大陆 IP 上传文件的场景。