# C2数据服务器部署说明

## 环境配置完成 ✅

您的C2数据服务器已经成功配置并运行！

## 文件结构

```
/home/
├── c2_data_server.py          # 主服务器程序
├── config.production.json     # 生产环境配置文件
├── requirements.txt           # Python依赖包列表
├── start_c2_server.sh        # 启动脚本
├── c2_env/                   # Python虚拟环境
└── README.md                 # 本说明文件
```

## 服务器状态

- ✅ **Python环境**: Python 3.12.3 + 虚拟环境
- ✅ **依赖包**: aiohttp, aiofiles 已安装
- ✅ **配置文件**: config.production.json 已加载
- ✅ **日志源**: 
  - online (文件): `/home/irc_server/logs/user_activity.log`
  - cleanup (数据库): `/home/irc_server/logs/reports.db`
- ✅ **HTTP服务**: 运行在 `0.0.0.0:8888`
- ✅ **数据缓存**: SQLite数据库 `/tmp/c2_data_cache.db`

## 启动服务器

### 方法1: 使用启动脚本
```bash
cd /home
./start_c2_server.sh
```

### 方法2: 手动启动
```bash
cd /home
source c2_env/bin/activate
python3 c2_data_server.py
```

## API接口测试

### 健康检查
```bash
curl -H "X-API-Key: your-secret-key-here" http://localhost:8888/health
```

### 拉取数据
```bash
curl -H "X-API-Key: your-secret-key-here" http://localhost:8888/api/pull
```

### 查看统计
```bash
curl -H "X-API-Key: your-secret-key-here" http://localhost:8888/api/stats
```

## 当前数据状态

服务器已经成功读取到数据：
- 缓存记录: 2条
- 数据来源: cleanup日志（数据库）
- IP地址: 223.104.83.215, 14.19.132.125

## 配置说明

### API认证
- 当前API Key: `your-secret-key-here`
- 建议设置环境变量: `export C2_API_KEY="your-actual-key"`

### 日志源配置
服务器配置了两个日志源：
1. **online**: 从 `user_activity.log` 读取JOIN记录
2. **cleanup**: 从 `reports.db` 数据库读取清除记录

### 缓存配置
- 数据库文件: `/tmp/c2_data_cache.db`
- 最大缓存: 10,000条记录
- 高水位线: 8,000条 (80%)
- 低水位线: 2,000条 (20%)

## 服务管理

### 停止服务器
```bash
# 查找进程
ps aux | grep c2_data_server.py

# 杀掉进程
kill <PID>
```

### 查看日志
服务器日志直接输出到控制台，建议使用 `nohup` 或 `systemd` 进行后台运行。

## 故障排除

1. **端口占用**: 如果8888端口被占用，检查 `netstat -tlnp | grep 8888`
2. **权限问题**: 确保对 `/tmp/` 目录有写权限
3. **依赖问题**: 重新激活虚拟环境 `source c2_env/bin/activate`

## 部署完成 🎉

您的C2数据服务器已经成功配置并运行，可以开始传输日志数据到平台了！
