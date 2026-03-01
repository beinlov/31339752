# 🔧 地区名称统一 Bug 修复指南

## 📋 修复的问题

1. ✅ **地区命名不统一**: "广西壮族自治区" → "广西", "中国台湾" → "台湾"
2. ✅ **后台管理系统tooltip显示为0**: 改进图表tooltip显示逻辑

---

## 🔨 修改的文件

### 后端
- `backend/stats_aggregator/aggregator.py` - 统一地名处理

### 前端
- `fronted/src/components/centerPage/charts/options.js` - 修正地名映射
- `fronted/src/components/NodeManagement.js` - 改进tooltip

---

## 🚀 应用修复（3步）

### 步骤1: 重新聚合数据

```bash
cd ~/botnet/backend/stats_aggregator
python aggregator.py once
```

### 步骤2: 重新构建前端

```bash
cd ~/botnet/fronted
npm run build
```

### 步骤3: 重启服务

```bash
# 直接部署
cd ~/botnet/test
bash stop-services.sh
bash start-services.sh

# 或 Docker部署
cd ~/botnet/test
docker-compose -f docker-compose.dev.yml restart
```

---

## ✅ 验证修复

### 1. 检查数据库

```sql
-- 进入MySQL
mysql -u botnet -p botnet_db

-- 检查省份名称（应该看到"广西"而不是"广西壮族自治区"）
SELECT DISTINCT province FROM china_botnet_ramnit ORDER BY province;

-- 检查国家名称（应该看到"台湾"而不是"中国台湾"）
SELECT DISTINCT country FROM global_botnet_ramnit ORDER BY country;
```

### 2. 测试API

```bash
# 测试API返回
curl http://localhost:8000/api/node-stats/ramnit | jq '.data.country_distribution'

# 应该返回：
# {
#   "中国": 1500,
#   "台湾": 50,     # 不是"中国台湾"
#   "美国": 100
# }
```

### 3. 检查前端

#### 处置平台
- 访问 http://服务器IP/disposal
- 查看左侧列表和地图
- ✅ 应显示"广西"、"台湾"且数量一致

#### 后台管理系统
- 访问 http://服务器IP/admin
- 进入节点管理
- 鼠标悬停在饼状图上
- ✅ **应显示正确数量**（如"中国: 1500 (75%)"）

---

## 🐛 故障排查

### 问题: 仍显示旧地名

```bash
# 清空聚合表重新聚合
mysql -u botnet -p -e "
USE botnet_db;
DELETE FROM china_botnet_ramnit;
DELETE FROM global_botnet_ramnit;
"

# 重新聚合
cd ~/botnet/backend/stats_aggregator
python aggregator.py once
```

### 问题: Tooltip仍显示0

```bash
# 清除浏览器缓存
# 按 Ctrl + Shift + Delete

# 或重新构建前端
cd ~/botnet/fronted
rm -rf dist
npm run build
```

---

## 📊 预期效果

| 位置 | 修复前 | 修复后 |
|------|--------|--------|
| 左侧列表 | "广西壮族自治区" | "广西" |
| 左侧列表 | "中国台湾" | "台湾" |
| 地图显示 | 数量为0 | 显示正确数量 |
| Tooltip | 显示0 | 显示实际数量 |
| 数据一致性 | 不一致 | 完全一致 |

---

**修复完成！** 🎉
