#!/usr/bin/env python3
"""
网关侧间歇性丢包策略脚本
从主机API获取丢包策略并应用到iptables
"""
import subprocess
import time
import json
import requests
import os

# 配置项
API_BASE_URL = "http://192.168.137.1:8000"  # 本地控制平台地址（修改为实际IP）
API_ENDPOINT = "/api/suppression/packet-loss/export"  # 丢包策略导出接口
CHECK_INTERVAL = 10  # 检查间隔（秒）

class HttpDynamicDropper:
    def __init__(self, api_url, check_interval=10):
        self.api_url = api_url
        self.check_interval = check_interval
        self.chain_name = "INTERMITTENT_DROP"
        # 存储当前生效的 {ip: rate} 映射
        self.current_policies = {}

    def _run_cmd(self, cmd):
        """执行 iptables 命令"""
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError:
            return False

    def setup_env(self):
        """初始化 iptables 环境"""
        print(f"[*] 初始化策略链: {self.chain_name}")
        # 清理旧环境
        self._run_cmd(['iptables', '-D', 'FORWARD', '-j', self.chain_name])
        self._run_cmd(['iptables', '-F', self.chain_name])
        self._run_cmd(['iptables', '-X', self.chain_name])

        # 创建并挂载
        self._run_cmd(['iptables', '-N', self.chain_name])
        self._run_cmd(['iptables', '-I', 'FORWARD', '1', '-j', self.chain_name])

    def fetch_policy(self):
        """从主机API获取丢包策略"""
        try:
            response = requests.get(self.api_url, timeout=10)
            response.raise_for_status()

            # API返回JSON格式: {"ip1": 0.3, "ip2": 0.5}
            policies = response.json()

            if isinstance(policies, dict):
                return policies
            else:
                print(f"[!] API返回格式错误，预期dict，实际: {type(policies)}")
                return None

        except Exception as e:
            print(f"[!] 从API获取策略失败: {e}")
            return None

    def apply_rule(self, ip, rate, action="ADD"):
        """精准应用带概率的丢包规则"""
        flag = "-A" if action == "ADD" else "-D"
        # 同时作用于进入和发出的流量
        cmds = [
            ['iptables', flag, self.chain_name, '-d', ip, '-m', 'statistic', '--mode', 'random', '--probability', str(rate), '-j', 'DROP'],
            ['iptables', flag, self.chain_name, '-s', ip, '-m', 'statistic', '--mode', 'random', '--probability', str(rate), '-j', 'DROP']
        ]
        for cmd in cmds:
            self._run_cmd(cmd)

    def synchronize(self):
        """对比并同步策略"""
        new_policies = self.fetch_policy()
        if new_policies is None:
            return

        # 1. 移除已不在列表或概率发生变化的 IP
        for ip, rate in list(self.current_policies.items()):
            if ip not in new_policies or new_policies[ip] != rate:
                self.apply_rule(ip, rate, "DELETE")
                del self.current_policies[ip]
                print(f"[-] 移除规则: {ip}")

        # 2. 增加新 IP 或应用更新后的概率
        for ip, rate in new_policies.items():
            if ip not in self.current_policies:
                self.apply_rule(ip, rate, "ADD")
                self.current_policies[ip] = rate
                print(f"[+] 激活规则: {ip} (丢包率: {rate*100}%)")

    def run(self):
        if os.geteuid() != 0:
            print("[-] 必须使用 sudo 运行")
            return

        self.setup_env()
        print("=" * 60)
        print("间歇性丢包策略同步脚本已启动")
        print(f"API地址: {self.api_url}")
        print(f"同步间隔: {self.check_interval}秒")
        print(f"策略链: {self.chain_name}")
        print("=" * 60)

        try:
            while True:
                self.synchronize()
                time.sleep(self.check_interval)
        except KeyboardInterrupt:
            print("\n[*] 正在清理规则并退出...")
            self._run_cmd(['iptables', '-D', 'FORWARD', '-j', self.chain_name])
            self._run_cmd(['iptables', '-F', self.chain_name])
            self._run_cmd(['iptables', '-X', self.chain_name])

if __name__ == "__main__":
    # 构建完整的API URL
    full_url = f"{API_BASE_URL}{API_ENDPOINT}"
    dropper = HttpDynamicDropper(full_url, check_interval=CHECK_INTERVAL)
    dropper.run()