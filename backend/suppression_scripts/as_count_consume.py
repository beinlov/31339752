
"""
每个“序列”包含三次请求（vc1 -> vc2 -> ql=b2）
在收到每一步响应后继续下一步，整个序列视为一个并发单元。
 python as_count_consume.py -u http://192.168.55.123:80/content/faq.php -r 50 -c 100 -d 60
"""

import asyncio
import aiohttp
import argparse
import time
from itertools import cycle

VC1_LIST = [
    "6db629b06b47acbb48667c1d1d46e22af96d14b4e896a21bd11048cf8095a531b732c06668961bd76a7277dd64c741e56c6afe2bfdf014ae10bcdcd1eaa98d7711ae3633731ec68e6b2d4d1df5e4b064f7313fa102c547c6820e3c21ba3f4b653186b218a09bc53751cf25a010c75c4f9476f23811b0be556cb6f51a3b46d22c",
    "bcca9c0f44cf705b721508950631daa2f8cfa96720d2952fa11ea47e7381321eb9b9c38484b899043dd7d9b6e3606fb6fce1bdbc4aebe01495c5d436a75f3557adc7b9bf9b1682bb38f5631c69f4738ebef4a685fc734e70a7b9175b9982582c031edf91c6aacc3bf70fd1395e756c9116a66775c3e5e4d9f1853865cc45d4cb",
    "0f9c257cecf9c0ec3fca8db2fcb988cac70f498133ddb0525d888ae58ab9cca5501a129ab1885d8f00426b7c555999b8fc99ec7cf6c2d5acbd8c5345e2daeb8a5ade5d271681d2eb6a5e0f5e6af0d47f45130711565af79b6f08d639dc8b7e7cb26bbaa90a75358a8b5d5d48d8fdb57bdeef4a0876297f4d06fbf3b01f8fde38",
    "efb618ad36f1702ceea57d4a7838d46d6cd121740a2eb18612ec7f67501554094c1133e06d64ae69f41c64c8730b8c90e8a1df1d325f4dba7135ebe2683c13e96fe7cd498989348d14f14e0d9861649c6ba0ce7638aabdec384664fd862dd12bafb751d02fe29582d1afe6614f8d03eb4fc7911189245ef4dea19cdb56cb5928",
    "f0e947ea16b85c69cfdd451eb240e96d4a04ead8469ec2baca0b43be32e0e34f7ed3adc8f70d6d3d00f2d844beb1aa4ffc6a43b1adadc189e47b94de15291d4385c3b414655fc5ef2f2d688fc1fc927e7bef7ba5870447fb2ef116314904d627b9add26dfe32943ef04a57edbec365114c2cceabe9bb7b118223a0d8ea6d7257",
    "af2ab05432b65c73af08e5c1433961c16e4319b8ca0e05fae1c4e87a21f9a79e3fd3b918727a9b39d9ec89cfa3382d0034cc21e101283e9fdd2f44da8d9289ead04dafcd29875aac9d4d0c7e7e8fdb9f3079938180b45ee9134590e5b7143f50636d9e8f819293ef809c1ce9adf24760f25fb2bb5022513768fc80fdf60d6ff2"
]

VC2_LIST = [
    "b4e35866512bec34d232dd5ccc900136b9bf25c64a69a918bef65bdf5de478af4885ba5724c87e3cefb8c369071f1ae3e06288e596947cfdc9868b9da46be9e497046c1fb4a6c904bb547db63376098a6264655405e5d96247a4f244dcbf138f38fcb73cc02a317d4b80c5de56b45a8c535c94719e9b4c125bc4814b36578",
    "023684b93561200d6b41ad5cb6f9ef87da94decaf210c66b15b30735a38536e3f176a049cdc338d80ec7ac731e05dd926fbe78dd0b20e0adc3a60842374ab7f38a1c9981dc23de80e8c930a6c99f0957f4e35aafe89d612f1e533d89b0abdedc3a80c7ed58f52c4ae44231c4416b91c97003f7fb8eac1063acda493b44f02881",
    "8d8e77d67f1066491fad8cd9e15433d0f6eb5aead8de358df969bfd1e0912440f42379e598b3a58e2c4aca1f8e3fc20fbfaab495b85983783fb5997e4a40a5d1177c86e48f7e6a6d7e6d6b4a0bff28de948302e40dd11464997de323a05ef86fa83025664f8ea096d097b8ba79cffeddc433e8fbcb4fc0c8967320d7802c74ea",
    "f607a42d5c8e8ab91191512f3638365df00449eaa57f23271bd0edfd999c3e04fc40077d9acedcd521d8c9b2bc6ccc3b260790b77de44c96cfa97b914120def1123c420843ad57df6c1999a29934ea6a4f2fb210bc3d7a52ea245adb68c881e1cf369b6510af05804fdb033725f7ba8250ce5de1e569cd0b1012e44f880eccf3",
    "3ac52e5b8efdfac0c3ad4d8d3e659e04d93d5299bd889c9b9f423adc21c2157adf535a61721400d3e9c2bbc7e518176c999c9941a51e298c155b9e602aa4dd2cd028c25a30e139ade7a91579d0687b798e228242939dceeec0419dc86a7352b307e58d1b26d506f00f6d214415b48bc38e6ed611b42e110229ac5d8a295f9df5",
    "bb66875c2f93884b7c30d1434591b2b5bf3f2e4789b4ea76d17731815081cd7677a690fcd2b083693cb16f083beeb49c0fed4b8fab7118021ad15d33cc447caa0da7b4128f42e524b1c77c2c895d5f0875e1a032b21e4a6c454c07fbedb7474b5c13bc11c2a3cdf82971e44bd81c9f84f01096ad52ad72ed95f34ef2681801b0",
    "16fb5628f2a2bf645789a48f1843f813e2684d7823ebc20b310e8baaa33b7814bab2f95c46f86a4e9dd3087b37adf4815d305a707748062ced4d8c57fceb0012c7ea33f2d45f05a2e264b5632ffd3001b633cfaff4b72a650bdd927b0128a61cae8fdb6f4fe5040b45693ad3a9ab1f085a3c97c6c1d793c8eadc1be8b1a3a621"
   ]

# 轮询器
vc1_cycle = cycle(VC1_LIST)
vc2_cycle = cycle(VC2_LIST)

# ql 参数固定为 b2
QL_PARAM = "b2"

async def send_get(session, url, params, timeout=15):
    """通用 GET 请求封装，返回状态码与文本（若成功）"""
    try:
        async with session.get(url, params=params, timeout=timeout) as resp:
            text = await resp.text()
            return resp.status, text
    except asyncio.TimeoutError:
        return None, "timeout"
    except Exception as e:
        return None, str(e)

async def send_sequence(session, url, vc1_value, vc2_value, seq_id=None):
    """
    发送完整序列：vc1 -> vc2 -> ql=a5
    在每一步收到响应后继续下一步。
    """
    prefix = f"[Seq {seq_id}]" if seq_id is not None else "[Seq]"
    # 第一步：vc1
    params1 = {'vc1': vc1_value}
    status1, text1 = await send_get(session, url, params1)
    print(f"{prefix} vc1 sent, status={status1}, len_resp={len(text1) if text1 else 0}")
    if status1 is None:
        print(f"{prefix} vc1 请求失败：{text1}，序列终止。")
        return

    # 第二步：vc2
    params2 = {'vc2': vc2_value}
    status2, text2 = await send_get(session, url, params2)
    print(f"{prefix} vc2 sent, status={status2}, len_resp={len(text2) if text2 else 0}")
    if status2 is None:
        print(f"{prefix} vc2 请求失败：{text2}，序列终止。")
        return

    # 第三步：ql=b2
    params3 = {'ql': QL_PARAM}
    status3, text3 = await send_get(session, url, params3)
    print(f"{prefix} ql={QL_PARAM} sent, status={status3}, len_resp={len(text3) if text3 else 0}")

async def worker_loop(url, rate, duration, concurrency):
    """
    rate: 每秒启动多少个序列（不是单次请求）
    concurrency: 同时运行多少个序列
    """
    connector = aiohttp.TCPConnector(limit=0)  # 交给信号量控制并发；不限制连接数
    semaphore = asyncio.Semaphore(concurrency)
    seq_counter = 0
    async with aiohttp.ClientSession(connector=connector) as session:
        start_time = time.time()
        try:
            while True:
                # 检查是否到达时长上限
                if duration and (time.time() - start_time) >= duration:
                    print("[*] 设定时间已到，任务结束。")
                    break

                # 控速：每 1/rate 秒发起一个新的序列
                # 但先尝试获取一个并发槽位（若没有则等待）
                await semaphore.acquire()
                seq_counter += 1
                seq_id = seq_counter

                # 从轮询器中获取 vc1 / vc2
                vc1_value = next(vc1_cycle)
                vc2_value = next(vc2_cycle)

                # 在后台执行序列，并在完成后释放 semaphore
                async def run_and_release(sid, v1, v2):
                    try:
                        await send_sequence(session, url, v1, v2, seq_id=sid)
                    finally:
                        semaphore.release()

                asyncio.create_task(run_and_release(seq_id, vc1_value, vc2_value))

                # 按速率等候
                await asyncio.sleep(0 if rate <= 0 else 1.0 / rate)

        except asyncio.CancelledError:
            print("[*] worker_loop 被取消。")
        except KeyboardInterrupt:
            print("\n[*] 手动停止，程序退出。")

def main():
    parser = argparse.ArgumentParser(description="Asruex 固定 VC1/VC2 顺序模拟器（vc1->vc2->ql=a5）")
    parser.add_argument("-u", "--url", required=True,
                        help="目标 C2 URL，例如 http://192.168.55.2:80/content/faq.php")
    parser.add_argument("-r", "--rate", type=float, default=10.0,
                        help="每秒启动的序列数，默认 10")
    parser.add_argument("-c", "--concurrency", type=int, default=10,
                        help="并发序列数，默认 10")
    parser.add_argument("-d", "--duration", type=int, default=0,
                        help="持续时间（秒），默认 0 表示无限")
    args = parser.parse_args()

    if not args.url.startswith("http://") and not args.url.startswith("https://"):
        args.url = "http://" + args.url

    print(f"[*] 目标 URL：{args.url}")
    print(f"[*] 每秒启动序列数：{args.rate} 个/秒")
    print(f"[*] 并发序列数：{args.concurrency}")
    if args.duration:
        print(f"[*] 持续时间：{args.duration} 秒")
    print("[*] 按 Ctrl+C 停止程序。")

    try:
        asyncio.run(worker_loop(args.url, args.rate, args.duration, args.concurrency))
    except KeyboardInterrupt:
        print("\n[*] 手动停止，程序退出。")

if __name__ == "__main__":
    main()
