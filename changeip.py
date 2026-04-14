import os
import time
import boto3
import re
import subprocess
import logging
import ipaddress
import signal
import json
import urllib.request
from collections import deque
from botocore.exceptions import ClientError
from botocore.config import Config

# AWS 配置
AWS_REGION = "us-east-2"
INSTANCE_ID = "i-0edf3378b3cdc3d49"

# OpenVPN 配置
LOCAL_CONFIG_PATH = "/etc/openvpn/client.conf"

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("eip_manager.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

allocated_ips = deque()

# IP 地址格式验证函数
def is_valid_ipv4(ip):
    try:
        ipaddress.IPv4Address(ip)
        return True
    except:
        return False

def fetch_existing_eips():
    ec2 = boto3.client("ec2", region_name=AWS_REGION)
    try:
        response = ec2.describe_addresses()
        global allocated_ips
        allocated_ips = deque([
            (ip.strip(), addr["AllocationId"])
            for addr in response["Addresses"]
            if (ip := addr.get("PublicIp")) and is_valid_ipv4(ip)
            if "AllocationId" in addr
        ])
        logging.info(f"当前已分配的 EIP: {list(allocated_ips)}")
    except ClientError as e:
        logging.error(f"获取 EIP 列表失败: {e}")

# 超时处理器（释放 EIP 时防卡死）
def timeout_handler(signum, frame):
    raise TimeoutError("释放 EIP 超时")

def get_new_ip():
    boto_config = Config(
        connect_timeout=3,
        read_timeout=5,
        retries={'max_attempts': 2}
    )
    ec2 = boto3.client("ec2", region_name=AWS_REGION, config=boto_config)

    if len(allocated_ips) >= 5:
        old_ip, old_alloc_id = allocated_ips.popleft()
        try:
            response = ec2.describe_addresses(PublicIps=[old_ip])
            addresses = response.get("Addresses", [])
            if addresses and "AssociationId" in addresses[0]:
                assoc_id = addresses[0]["AssociationId"]
                logging.info(f"发现 IP {old_ip} 有绑定，先解除 AssociationId: {assoc_id}")
                ec2.disassociate_address(AssociationId=assoc_id)
                time.sleep(2)
            logging.info(f"释放旧 IP: {old_ip}, AllocationId: {old_alloc_id}")
            ec2.release_address(AllocationId=old_alloc_id)
            logging.info(f"释放成功: {old_ip}")
        except ClientError as e:
            logging.error(f"释放失败: {e}")
        except Exception as e:
            logging.error(f"释放出错: {e}")

    try:
        logging.info("申请新的 EIP...")
        response = ec2.allocate_address(Domain="vpc")
        new_ip, allocation_id = response["PublicIp"], response["AllocationId"]
        allocated_ips.append((new_ip, allocation_id))
        logging.info(f"申请成功: {new_ip}")
        return new_ip, allocation_id
    except ClientError as e:
        if e.response["Error"]["Code"] == "AddressLimitExceeded":
            logging.warning("已达到 EIP 配额上限")
            return None, None
        logging.error(f"申请 EIP 失败: {e}")
        return None, None

def associate_ip(public_ip, allocation_id):
    ec2 = boto3.client("ec2", region_name=AWS_REGION)
    try:
        ec2.associate_address(InstanceId=INSTANCE_ID, AllocationId=allocation_id)
        logging.info(f"绑定 IP 成功: {public_ip}")
    except ClientError as e:
        logging.error(f"绑定 IP 失败: {e}")

def update_ovpn_config(new_ip):
    try:
        with open(LOCAL_CONFIG_PATH, "r", encoding="utf-8") as file:
            config = file.read()
        current_match = re.search(r"remote\s+(\d+\.\d+\.\d+\.\d+)\s+1194", config)
        if current_match and current_match.group(1) == new_ip:
            logging.info("配置中已是当前 IP，跳过更新")
            return
        new_config = re.sub(r"remote\s+\d+\.\d+\.\d+\.\d+\s+1194", f"remote {new_ip} 1194", config)
        with open(LOCAL_CONFIG_PATH, "w", encoding="utf-8") as file:
            file.write(new_config)
        logging.info(f"OpenVPN 配置已更新: {new_ip}")
    except Exception as e:
        logging.error(f"更新 OpenVPN 配置失败: {e}")

def restart_openvpn():
    try:
        logging.info("重启 OpenVPN 客户端...")
        subprocess.run(["sudo", "pkill", "openvpn"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(5)
        subprocess.Popen(["sudo", "openvpn", "--config", LOCAL_CONFIG_PATH], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        logging.info("OpenVPN 客户端已重启")
        update_aws_ip_routes()
    except Exception as e:
        logging.error(f"重启 OpenVPN 失败: {e}")

def update_aws_ip_routes():
    try:
        logging.info("正在更新 AWS IP 路由（绕过 VPN）...")
        with urllib.request.urlopen("https://ip-ranges.amazonaws.com/ip-ranges.json", timeout=10) as response:
            data = json.loads(response.read())
        result = subprocess.run(["ip", "route"], stdout=subprocess.PIPE, text=True)
        default_gateway = None
        for line in result.stdout.splitlines():
            if line.startswith("default"):
                default_gateway = line.split()[2]
                break
        if not default_gateway:
            logging.warning("未找到默认网关，无法设置路由")
            return
        prefixes = [
            entry["ip_prefix"]
            for entry in data["prefixes"]
            if entry["region"] == AWS_REGION and entry["service"] in ("EC2", "AMAZON")
        ]
        for cidr in prefixes:
            try:
                subprocess.run(["sudo", "ip", "route", "add", cidr, "via", default_gateway], check=True,stderr=subprocess.DEVNULL)

            except subprocess.CalledProcessError:
                pass
                
    except Exception as e:
        logging.error(f"更新 AWS 路由失败: {e}")

def wait_for_aws_connectivity(timeout=120, interval=5):
    ec2 = boto3.client("ec2", region_name=AWS_REGION)
    start = time.time()
    while time.time() - start < timeout:
        try:
            ec2.describe_account_attributes()
            logging.info("网络恢复，可以连接 AWS API")
            return
        except Exception as e:
            logging.info(f"等待 AWS 连通中... ({str(e)})")
            time.sleep(interval)
    logging.error("等待 AWS 连通超时，跳过本轮操作")

def main():
    fetch_existing_eips()
    while True:
        logging.info("开始更换 OpenVPN 服务器 IP")
        wait_for_aws_connectivity()
        new_ip, allocation_id = get_new_ip()
        if new_ip is None:
            logging.warning("无法获取新 IP，跳过本轮")
            time.sleep(600)
            continue
        associate_ip(new_ip, allocation_id)
        restart_openvpn()
        logging.info("等待网络恢复后继续下一次转换...")
        wait_for_aws_connectivity()
        logging.info("等待 10 分钟后继续下一次转换...")
        time.sleep(600)

if __name__ == "__main__":
    main()
