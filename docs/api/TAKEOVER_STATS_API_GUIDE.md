# 接管节点统计数据API接口文档

## 概述

本API提供僵尸网络接管节点的统计数据查询服务，为其他业务方提供标准化的数据接口。数据每分钟自动更新一次，确保数据的实时性和准确性。

## 基础信息

- **Base URL**: `http://your-domain/api/takeover-stats`
- **数据格式**: JSON
- **更新频率**: 每分钟
- **数据保留**: 7天历史数据

## 统计数据说明

### 数据指标定义

| 指标名称 | 说明 | 数据来源 |
|---------|------|----------|
| `total_nodes` | 已接管节点总数 | 所有botnet_nodes_*表中总的条目数 |
| `total_domestic_nodes` | 已接管国内节点总数 | 所有botnet_nodes_*表中is_china=1的总数 |
| `total_foreign_nodes` | 已接管国外节点总数 | 所有botnet_nodes_*表中is_china=0的总数 |
| `monthly_total_nodes` | 近一个月接管节点总数 | 所有botnet_nodes_*表中created_time为近30天且status=active的总数 |
| `monthly_domestic_nodes` | 近一个月接管国内节点数 | 所有botnet_nodes_*表中created_time为近30天且status=active且is_china=1的总数 |
| `monthly_foreign_nodes` | 近一个月接管国外节点数 | 所有botnet_nodes_*表中created_time为近30天且status=active且is_china=0的总数 |
| `cleaned_total_nodes` | 已清除节点总数 | 所有botnet_nodes_*表中status=cleaned的总条目数 |
| `cleaned_domestic_nodes` | 已清除国内节点总数 | 所有botnet_nodes_*表中status=cleaned且is_china=1的总数 |
| `cleaned_foreign_nodes` | 已清除国外节点总数 | 所有botnet_nodes_*表中status=cleaned且is_china=0的总数 |
| `monthly_cleaned_total_nodes` | 近一个月清除节点总数 | 所有botnet_nodes_*表中created_time为近30天且status=cleaned的总数 |
| `monthly_cleaned_domestic_nodes` | 近一个月清除国内节点数 | 所有botnet_nodes_*表中created_time为近30天且status=cleaned且is_china=1的总数 |
| `monthly_cleaned_foreign_nodes` | 近一个月清除国外节点数 | 所有botnet_nodes_*表中created_time为近30天且status=cleaned且is_china=0的总数 |
| `suppression_total_count` | 已使用抑制阻断策略总次数 | 固定值（暂时写死） |
| `monthly_suppression_count` | 近一个月使用抑制阻断策略次数 | 固定值（暂时写死） |

## API接口列表

### 1. 获取最新统计数据

**接口地址**: `GET /api/takeover-stats/latest`

**功能描述**: 获取最新的接管节点统计数据

**请求参数**: 无

**响应示例**:
```json
{
  "status": "success",
  "data": {
    "total_stats": {
      "total_nodes": 1420000,
      "total_domestic_nodes": 448160,
      "total_foreign_nodes": 968040
    },
    "monthly_stats": {
      "monthly_total_nodes": 3,
      "monthly_domestic_nodes": 1,
      "monthly_foreign_nodes": 2
    },
    "cleaned_stats": {
      "cleaned_total_nodes": 9,
      "cleaned_domestic_nodes": 7,
      "cleaned_foreign_nodes": 8
    },
    "monthly_cleaned_stats": {
      "monthly_cleaned_total_nodes": 6,
      "monthly_cleaned_domestic_nodes": 4,
      "monthly_cleaned_foreign_nodes": 5
    },
    "suppression_stats": {
      "suppression_total_count": 20,
      "monthly_suppression_count": 20
    },
    "timestamp": "2026-03-06T11:25:00.000Z",
    "updated_at": "2026-03-06T11:25:00.000Z"
  },
  "message": "获取最新统计数据成功"
}
```

### 2. 获取详细统计数据

**接口地址**: `GET /api/takeover-stats/detail`

**功能描述**: 获取按僵尸网络类型分类的详细统计数据

**请求参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `botnet_type` | string | 否 | 指定僵尸网络类型，不指定则返回所有类型 |

**响应示例**:
```json
{
  "status": "success",
  "data": [
    {
      "botnet_type": "asruex",
      "total_stats": {
        "total_nodes": 800000,
        "total_domestic_nodes": 250000,
        "total_foreign_nodes": 550000
      },
      "monthly_stats": {
        "monthly_total_nodes": 2,
        "monthly_domestic_nodes": 1,
        "monthly_foreign_nodes": 1
      },
      "cleaned_stats": {
        "cleaned_total_nodes": 5,
        "cleaned_domestic_nodes": 3,
        "cleaned_foreign_nodes": 2
      },
      "monthly_cleaned_stats": {
        "monthly_cleaned_total_nodes": 3,
        "monthly_cleaned_domestic_nodes": 2,
        "monthly_cleaned_foreign_nodes": 1
      },
      "suppression_stats": {
        "suppression_total_count": 20,
        "monthly_suppression_count": 20
      },
      "timestamp": "2026-03-06T11:25:00.000Z",
      "updated_at": "2026-03-06T11:25:00.000Z"
    }
  ],
  "count": 1,
  "message": "获取详细统计数据成功"
}
```

### 3. 获取历史统计数据

**接口地址**: `GET /api/takeover-stats/history`

**功能描述**: 获取历史统计数据，用于趋势分析

**请求参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `hours` | integer | 否 | 获取最近N小时的数据，默认24小时，最大168小时(7天) |
| `botnet_type` | string | 否 | 指定僵尸网络类型，不指定则返回总体数据 |

**响应示例**:
```json
{
  "status": "success",
  "data": [
    {
      "total_stats": {
        "total_nodes": 1420000,
        "total_domestic_nodes": 448160,
        "total_foreign_nodes": 968040
      },
      "monthly_stats": {
        "monthly_total_nodes": 3,
        "monthly_domestic_nodes": 1,
        "monthly_foreign_nodes": 2
      },
      "timestamp": "2026-03-06T09:39:00.000Z"
    }
  ],
  "count": 24,
  "time_range": {
    "start": "2026-03-05T10:39:00.000Z",
    "end": "2026-03-06T10:39:00.000Z",
    "hours": 24
  },
  "botnet_type": null,
  "message": "获取历史数据成功"
}
```

### 4. 获取统计摘要

**接口地址**: `GET /api/takeover-stats/summary`

**功能描述**: 获取统计数据摘要，包含排名和占比信息

**请求参数**: 无

**响应示例**:
```json
{
  "status": "success",
  "data": {
    "overview": {
      "total_nodes": 1420000,
      "total_domestic_nodes": 448160,
      "total_foreign_nodes": 968040,
      "monthly_total_nodes": 3,
      "monthly_domestic_nodes": 1,
      "monthly_foreign_nodes": 2
    },
    "rankings": [
      {
        "rank": 1,
        "botnet_type": "asruex",
        "total_nodes": 800000,
        "percentage": 56.34,
        "domestic_nodes": 250000,
        "foreign_nodes": 550000,
        "monthly_nodes": 2
      }
    ],
    "statistics": {
      "total_botnet_types": 5,
      "domestic_ratio": 31.56,
      "foreign_ratio": 68.44
    }
  },
  "message": "获取统计摘要成功"
}
```

### 5. 健康检查

**接口地址**: `GET /api/takeover-stats/health`

**功能描述**: 检查服务状态和数据更新情况

**请求参数**: 无

**响应示例**:
```json
{
  "status": "ok",
  "message": "服务正常",
  "database_connection": "ok",
  "latest_update": "2026-03-06T10:39:00.000Z",
  "record_count": 1440,
  "data_age_seconds": 45,
  "is_data_fresh": true
}
```

## 错误处理

### 错误响应格式

```json
{
  "detail": "错误描述信息"
}
```

### 常见错误码

| HTTP状态码 | 说明 |
|-----------|------|
| 200 | 请求成功 |
| 400 | 请求参数错误 |
| 404 | 数据不存在 |
| 500 | 服务器内部错误 |

## 使用示例

### Python示例

```python
import requests
import json

# 基础URL
base_url = "http://your-domain/api/takeover-stats"

# 获取最新统计数据
def get_latest_stats():
    response = requests.get(f"{base_url}/latest")
    if response.status_code == 200:
        data = response.json()
        print(f"总节点数: {data['data']['total_stats']['total_nodes']}")
        print(f"国内节点数: {data['data']['total_stats']['total_domestic_nodes']}")
        print(f"国外节点数: {data['data']['total_stats']['total_foreign_nodes']}")
    else:
        print(f"请求失败: {response.status_code}")

# 获取指定类型的详细数据
def get_detail_stats(botnet_type=None):
    params = {}
    if botnet_type:
        params['botnet_type'] = botnet_type
    
    response = requests.get(f"{base_url}/detail", params=params)
    if response.status_code == 200:
        data = response.json()
        for item in data['data']:
            print(f"类型: {item['botnet_type']}")
            print(f"节点数: {item['total_stats']['total_nodes']}")
    else:
        print(f"请求失败: {response.status_code}")

# 获取历史数据
def get_history_stats(hours=24):
    params = {'hours': hours}
    response = requests.get(f"{base_url}/history", params=params)
    if response.status_code == 200:
        data = response.json()
        print(f"获取到 {data['count']} 条历史记录")
        for item in data['data']:
            print(f"时间: {item['timestamp']}, 节点数: {item['total_stats']['total_nodes']}")
    else:
        print(f"请求失败: {response.status_code}")

# 使用示例
if __name__ == "__main__":
    get_latest_stats()
    get_detail_stats("asruex")
    get_history_stats(6)  # 获取最近6小时的数据
```

### JavaScript示例

```javascript
// 基础URL
const baseUrl = "http://your-domain/api/takeover-stats";

// 获取最新统计数据
async function getLatestStats() {
    try {
        const response = await fetch(`${baseUrl}/latest`);
        const data = await response.json();
        
        if (response.ok) {
            console.log(`总节点数: ${data.data.total_stats.total_nodes}`);
            console.log(`国内节点数: ${data.data.total_stats.total_domestic_nodes}`);
            console.log(`国外节点数: ${data.data.total_stats.total_foreign_nodes}`);
        } else {
            console.error('请求失败:', data.detail);
        }
    } catch (error) {
        console.error('网络错误:', error);
    }
}

// 获取详细统计数据
async function getDetailStats(botnetType = null) {
    try {
        let url = `${baseUrl}/detail`;
        if (botnetType) {
            url += `?botnet_type=${botnetType}`;
        }
        
        const response = await fetch(url);
        const data = await response.json();
        
        if (response.ok) {
            data.data.forEach(item => {
                console.log(`类型: ${item.botnet_type}`);
                console.log(`节点数: ${item.total_stats.total_nodes}`);
            });
        } else {
            console.error('请求失败:', data.detail);
        }
    } catch (error) {
        console.error('网络错误:', error);
    }
}

// 使用示例
getLatestStats();
getDetailStats("asruex");
```

### cURL示例

```bash
# 获取最新统计数据
curl -X GET "http://your-domain/api/takeover-stats/latest"

# 获取指定类型的详细数据
curl -X GET "http://your-domain/api/takeover-stats/detail?botnet_type=asruex"

# 获取最近6小时的历史数据
curl -X GET "http://your-domain/api/takeover-stats/history?hours=6"

# 获取统计摘要
curl -X GET "http://your-domain/api/takeover-stats/summary"

# 健康检查
curl -X GET "http://your-domain/api/takeover-stats/health"
```

## 数据更新机制

1. **自动聚合**: 系统每分钟自动执行一次数据聚合
2. **数据源**: 从所有`botnet_nodes_*`表中统计数据
3. **数据清理**: 自动清理7天前的历史数据
4. **故障恢复**: 聚合失败时会在下一个周期重试

## 性能说明

- **响应时间**: 通常在100ms以内
- **并发支持**: 支持高并发查询
- **缓存机制**: 数据库层面有适当的索引优化
- **数据一致性**: 保证数据的准确性和一致性

## 联系方式

如有问题或建议，请联系技术支持团队。

## 更新日志

- **v1.0.0** (2026-03-06): 初始版本发布
  - 提供基础统计数据查询功能
  - 支持按类型查询详细数据
  - 提供历史数据和趋势分析
  - 包含健康检查和服务监控
