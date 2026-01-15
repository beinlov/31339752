# 编码问题修复说明

## 问题描述

原启动脚本使用中文字符，在Windows批处理文件中遇到编码问题，导致：
- 中文显示为乱码
- 批处理命令无法正确执行
- 出现大量"不是内部或外部命令"错误

## 解决方案

已创建纯英文版本的启动脚本，避免编码问题：

- ✅ `start_all_v3.bat` - 英文版启动脚本
- ✅ `stop_all.bat` - 英文版停止脚本

## 使用方法

### 启动平台

```batch
start_all_v3.bat
```

### 停止服务

```batch
stop_all.bat
```

## 为什么会出现编码问题？

Windows批处理文件默认使用 **GBK/ANSI** 编码，但如果文件保存为 **UTF-8** 编码，中文字符会被错误解析，导致：

1. 中文被解析为乱码字符
2. 乱码字符被当作命令执行
3. 系统找不到这些"命令"，报错

## 修复内容

### 修复前（有中文，UTF-8编码）

```batch
echo 本脚本将启动以下服务:
echo   1. Redis Server      (端口: 6379)
```

运行时显示：
```
'嶇渚濊禆...' 不是内部或外部命令
```

### 修复后（纯英文）

```batch
echo This script will start the following services:
echo   1. Redis Server      (Port: 6379)
```

运行正常。

## 如果仍需要中文界面

有两种方法：

### 方法1: 手动转换编码

1. 用记事本打开 `start_all_v3.bat`
2. 点击"文件" -> "另存为"
3. 编码选择 "ANSI"
4. 保存

### 方法2: 在脚本开头添加UTF-8支持

```batch
@echo off
chcp 65001 >nul 2>&1
REM 后面可以使用中文
```

但这种方法不是100%可靠，推荐使用纯英文版本。

## 当前脚本功能

所有功能保持不变：

1. ✅ 自动检测Redis
2. ✅ 自动检测Python环境
3. ✅ 自动安装依赖
4. ✅ 自动检测Node.js（前端）
5. ✅ 按顺序启动5个服务
6. ✅ 显示详细的启动信息
7. ✅ 提供访问地址和日志位置

## 验证

运行后应该看到：

```
============================================================
   Botnet Platform - Startup Script v3.0
============================================================

This script will start the following services:
  1. Redis Server      (Port: 6379)
  2. Log Processor     (with Internal Worker)
  3. Platform Backend  (Port: 8000)
  4. Stats Aggregator  (Daemon, 30min interval)
  5. Frontend UI       (Port: 5173)

============================================================

[Step 1/6] Checking Redis status...
[OK] Redis is running

...

============================================================
   All Services Started Successfully!
============================================================
```

---

**问题已解决！** 现在可以正常使用一键启动脚本了。
