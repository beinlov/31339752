#!/bin/bash

# 用法：./route.sh src_ip dst_ip or ./route.sh 直接输入
# 检查root权限
if [[ $EUID -ne 0 ]]; then
   echo "需要root权限"
   exit 1
fi

# input IP1(原僵王ip) & IP2(接管CnC ip)
read -p "input source IP: " IP1
read -p "input target IP: " IP2

# input check, in case ip1 and ip2 is empty
if [[ -z "$IP1" || -z "$IP2" ]]; then
    echo "IP 地址不能为空！"
    exit 1
fi

# check ip format
if ! [[ $IP1 =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]] || ! [[ $IP2 =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "无效的 IP 地址格式！"
    exit 1
fi


# 转发，配置网关劫持
echo 1 > /proc/sys/net/ipv4/ip_forward

iptables -t nat -A PREROUTING -d $IP1 -j DNAT --to-destination $IP2

echo "已将发往 $IP1 的流量转发到 $IP2。"