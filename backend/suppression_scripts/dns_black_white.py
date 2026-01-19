import requests
import os
import subprocess
import time

# 配置信息
API_BASE_URL = "http://192.168.137.1:8000"  # 本地控制平台地址（修改为实际IP）
API_ENDPOINT = "/api/suppression/blacklist/domain/export"  # 远程域名黑名单同步接口
CONFIG_PATH = "/etc/dnsmasq.d/dns_blacklist.conf"
INTERVAL = 300  # 同步间隔时间（秒），默认5分钟


def update_blacklist():
    try:
        # 1. 从远程 API 获取域名黑名单列表
        url = f"{API_BASE_URL}{API_ENDPOINT}"
        response = requests.get(url, timeout=10)
        # 确保请求成功
        response.raise_for_status()

        # 假设 API 返回纯文本格式，每行一个域名
        domains = response.text.strip().split('\n')

        # 2. 转换为 dnsmasq 格式
        new_content = "# Auto-generated blacklist\n"
        count = 0
        for domain in domains:
            domain = domain.strip()
            if domain and not domain.startswith('#'):
                # 将域名指向 0.0.0.0 实现拦截
                new_content += f"address=/{domain}/0.0.0.0\n"
                count += 1

        # 3. 检查是否有更新 (避免重复重启服务)
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                current_file_content = f.read()
                if current_file_content == new_content:
                    print(f"[{time.strftime('%H:%M:%S')}] 远程黑名单未变化，跳过更新。")
                    return

        # 4. 写入配置文件
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            f.write(new_content)

        # 5. 重启 dnsmasq 服务以使配置生效
        print(f"[{time.strftime('%H:%M:%S')}] 检测到更新，正在重启 dnsmasq...")
        subprocess.run(["sudo", "systemctl", "restart", "dnsmasq"], check=True)

        print(f"成功更新 {count} 条域名记录。")

    except Exception as e:
        print(f"同步失败: {e}")


if __name__ == "__main__":
    print("=" * 60)
    print("DNS 域名黑名单自动同步脚本已启动")
    print(f"API 地址: {API_BASE_URL}{API_ENDPOINT}")
    print(f"同步频率: {INTERVAL} 秒 (约 {INTERVAL // 60} 分钟)")
    print(f"配置文件: {CONFIG_PATH}")
    print("=" * 60)

    while True:
        update_blacklist()
        time.sleep(INTERVAL)