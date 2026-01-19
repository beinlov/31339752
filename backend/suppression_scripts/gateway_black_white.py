import requests
import subprocess
import time
import signal
import sys

# 配置信息
API_BASE_URL = "http://192.168.137.1:8000"  # 本地控制平台地址（修改为实际IP）
API_ENDPOINT = "/api/suppression/blacklist/ip/export"  # IP 黑名单远程同步接口
INTERVAL = 60  # 同步间隔时间（秒）
SET_NAME = "blacklist_set"  # IPSET 集合名称


def run_cmd(cmd):
    """封装系统命令执行"""
    return subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def cleanup(signum=None, frame=None):
    """清理函数：只删除与本脚本相关的规则和集合"""
    print(f"\n[{time.strftime('%H:%M:%S')}] 脚本停止，正在清理防火墙规则...")
    # 1. 删除注入的 iptables 规则（只删除这一条，不影响原有的其他规则）
    run_cmd(["sudo", "iptables", "-D", "FORWARD", "-m", "set", "--match-set", SET_NAME, "dst", "-j", "DROP"])
    run_cmd(["sudo", "iptables", "-D", "OUTPUT", "-m", "set", "--match-set", SET_NAME, "dst", "-j", "DROP"])
    # 2. 销毁 IPSET 集合
    run_cmd(["sudo", "ipset", "destroy", SET_NAME])
    print("环境已清理，原有防火墙策略保持不变。")
    sys.exit(0)


def init_env():
    """初始化环境：确保安装了 ipset 并清理旧的残留规则"""
    print("正在初始化黑名单管控环境...")
    # 确保系统中安装了 ipset
    if run_cmd(["which", "ipset"]).returncode != 0:
        print("错误：未找到 ipset 工具，请先执行 sudo apt install ipset")
        sys.exit(1)

    # 如果上次异常退出，可能存在残留，先尝试清理
    run_cmd(["sudo", "iptables", "-D", "FORWARD", "-m", "set", "--match-set", SET_NAME, "dst", "-j", "DROP"])
    run_cmd(["sudo", "ipset", "destroy", SET_NAME])

    # 1. 创建 IPSET 集合（哈希类型，存储 IP 地址）
    run_cmd(["sudo", "ipset", "create", SET_NAME, "hash:ip"])

    # 2. 在 iptables 中插入第一条过滤规则，优先级最高
    # 该规则只匹配 SET_NAME 中的 IP，不匹配的流量会直接跳过，继续匹配原有的规则
    run_cmd(["sudo", "iptables", "-I", "FORWARD", "1", "-m", "set", "--match-set", SET_NAME, "dst", "-j", "DROP"])
    run_cmd(["sudo", "iptables", "-I", "OUTPUT", "1", "-m", "set", "--match-set", SET_NAME, "dst", "-j", "DROP"])
    print(f"黑名单集合 {SET_NAME} 已挂载到 iptables 转发和输出链。")


def update_blacklist():
    try:
        # 1. 从远程 API 获取 IP 黑名单列表
        url = f"{API_BASE_URL}{API_ENDPOINT}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        # API 返回纯文本格式，每行一个 IP
        ips = [ip.strip() for ip in response.text.strip().split('\n')
               if ip.strip() and not ip.startswith('#')]

        # 2. 全量原子更新：清空原有集合并重新添加，这样不需要重启 iptables
        run_cmd(["sudo", "ipset", "flush", SET_NAME])

        for ip in ips:
            run_cmd(["sudo", "ipset", "add", SET_NAME, ip])

        print(f"[{time.strftime('%H:%M:%S')}] 同步成功！当前黑名单包含 {len(ips)} 个 IP。")

    except Exception as e:
        print(f"同步失败: {e}")


if __name__ == "__main__":
    # 注册退出信号（Ctrl+C 或 kill 命令）
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    init_env()
    print("=" * 60)
    print("远程 IP 黑名单自动同步脚本已启动")
    print(f"API 地址: {API_BASE_URL}{API_ENDPOINT}")
    print(f"同步频率: {INTERVAL} 秒")
    print("=" * 60)

    try:
        while True:
            update_blacklist()
            time.sleep(INTERVAL)
    except Exception:
        cleanup()