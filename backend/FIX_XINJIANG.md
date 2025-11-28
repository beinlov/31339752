# 🔧 修复新疆地图显示问题

## 问题描述
地图上没有新疆的节点数据，鼠标移动到新疆后不显示感染节点数量。

## 原因分析

可能的原因：
1. **数据库中存储的是"新疆维吾尔自治区"，但地图需要的是"新疆"**
2. 聚合表中的province字段不统一
3. 前端数据匹配失败

## 🔍 第一步：诊断问题

```bash
cd d:\workspace\botnet\backend
python check_xinjiang.py
```

这个脚本会检查：
- ✓ 原始节点表中是否有新疆数据
- ✓ 聚合表中是否有新疆数据
- ✓ API会返回什么province名称

**示例输出**：

```
============================================================
新疆数据诊断
============================================================

[1] 检查原始节点表 (botnet_nodes_ramnit)...
  找到新疆相关数据:
    province = '新疆维吾尔自治区': 234 个节点  ← 找到了！

[2] 检查聚合表 (china_botnet_ramnit)...
  ⚠️ 聚合表中没有找到包含'新疆'的province数据  ← 问题在这里！
  
  聚合表中的省份分布 (前10):
    江苏: 1500 个节点
    广西: 601 个节点
    ...

[3] 模拟API返回数据...
  ❌ API返回的数据中没有包含'新疆'的省份
     这就是地图上新疆显示为0的原因！

============================================================
诊断结果和修复建议
============================================================

❌ 问题确认: 聚合表中没有'新疆'数据

可能的原因:
1. 原始数据中province字段是'新疆维吾尔自治区'
2. 聚合器在聚合时没有正确统一命名
3. 聚合表中保留了全称，导致前端匹配失败

修复方法:
运行以下命令:
  python fix_region_names.py
```

## 🔨 第二步：修复数据

```bash
cd d:\workspace\botnet\backend
python fix_region_names.py
```

这个脚本会：

### 1. 诊断问题（自动）
```
[1/5] 检查并诊断问题数据...

  检查表: botnet_nodes_ramnit
    ℹ️ 新疆相关数据:
       新疆维吾尔自治区: 234 个节点  ← 确认有数据
    ⚠️ 发现不规范的省份名称:
       新疆维吾尔自治区: 234 个节点  ← 需要修复
```

### 2. 修复原始数据
```
[2/5] 修复原始节点表中的数据...

  处理表: botnet_nodes_ramnit
    ✓ 更新 新疆维吾尔自治区: 234 行  ← 修复！
```

**修复操作**：
- "新疆维吾尔自治区" → "新疆"
- 同时修复其他不规范命名

### 3. 清空聚合表
```
[3/5] 清空旧的聚合表...
  清空表: china_botnet_ramnit
    ✓ 已清空 34 行
```

### 4. 重新聚合
```
[4/5] 重新聚合数据...
  聚合 ramnit...
    ✓ 中国表: 35 行
    ✓ 全球表: 15 行
```

### 5. 验证结果
```
[5/5] 验证修复结果...
  ✓ ramnit 省份名称已规范化
  ✓ ramnit 国家名称已规范化
  
  ramnit 省份分布 (35 个):
    1. 江苏: 1500 个节点
    2. 广西: 601 个节点
    3. 新疆: 234 个节点     ← 成功修复！
    ...
```

## 🔍 第三步：再次验证

```bash
# 再次运行诊断脚本
python check_xinjiang.py
```

**预期输出**：
```
[2] 检查聚合表 (china_botnet_ramnit)...
  找到新疆相关数据:
    province = '新疆': 234 个节点  ← 已统一为简称！

[3] 模拟API返回数据...
  ✓ API会返回: province='新疆', amount=234  ← 修复成功！
```

## 📝 第四步：前端更新

### 1. 重新构建前端
```bash
cd d:\workspace\botnet\fronted
npm run build
```

### 2. 重启服务
```bash
# 停止旧进程
Get-Process python | Where-Object {$_.Path -like "*botnet*"} | Stop-Process -Force

# 重新启动
cd d:\workspace\botnet\backend
python main.py
```

### 3. 清除浏览器缓存
- 按 `Ctrl + Shift + Delete`
- 或使用无痕模式访问

## ✅ 验证修复效果

### 1. 测试API
```bash
# PowerShell中测试
Invoke-WebRequest http://localhost:8000/api/province-amounts?botnet_type=ramnit | Select-Object -ExpandProperty Content | ConvertFrom-Json | Select-Object -ExpandProperty ramnit | Where-Object {$_.province -like "*新疆*"}

# 应该返回:
# province : 新疆
# amount   : 234
```

### 2. 检查前端

#### 处置平台 (http://localhost/disposal)
1. 打开浏览器开发者工具（F12）
2. 查看Console，不应该有：`未能匹配省份: "新疆维吾尔自治区"`
3. 鼠标移动到地图上的新疆
4. ✅ 应该显示：新疆地区有颜色（不是灰色）
5. ✅ 鼠标悬停应该显示：234个节点

#### 后台管理系统 (http://localhost:3000/admin)
- 国家分布中应该看到中国的数据包含了新疆的节点

## 🐛 故障排查

### 问题1: 修复后仍然没有新疆数据

**检查1**: 数据库中是否真的有新疆数据
```bash
python check_xinjiang.py
```

如果输出显示：
```
⚠️ 原始表中没有找到包含'新疆'的province数据
```

说明原始数据中确实没有新疆的节点。这是正常的。

**检查2**: 是否有其他拼写
数据库中可能存储为：
- "新疆" ✓
- "新疆维吾尔自治区" → 需要修复
- "新疆自治区" → 需要修复
- "Xinjiang" → 可能是英文数据

### 问题2: 前端仍然不显示

**解决方法**：
```bash
# 1. 强制清除前端缓存重新构建
cd d:\workspace\botnet\fronted
rm -rf dist node_modules/.cache
npm run build

# 2. 硬刷新浏览器
# 按 Ctrl + Shift + R（不是普通的F5）

# 3. 检查浏览器控制台
# 打开F12，看Network标签
# 检查API返回的数据是否包含新疆
```

### 问题3: 地图JSON可能没有新疆

**检查地图JSON**：
```bash
# 查看地图JSON文件
cat d:\workspace\botnet\fronted\src\china.json | grep "新疆"
```

如果找不到"新疆"，说明地图JSON文件本身就没有新疆数据。这是地图资源的问题，不是数据问题。

## 📊 数据流程说明

完整的数据流向：

```
原始数据表 (botnet_nodes_ramnit)
├─ province: "新疆维吾尔自治区"  ← 原始数据
│
↓ [聚合器统一命名]
│
聚合表 (china_botnet_ramnit)
├─ province: "新疆"              ← 统一后的数据
│
↓ [API返回]
│
前端 (JavaScript)
├─ API返回: {province: "新疆", amount: 234}
│
↓ [provinceNameMap映射]
│
地图显示
├─ 匹配 '新疆维吾尔自治区' → '新疆'
└─ 显示新疆区域的节点数量
```

## 🎯 总结

修复新疆显示问题的完整流程：

```bash
# 1. 诊断问题
python check_xinjiang.py

# 2. 修复数据
python fix_region_names.py

# 3. 验证修复
python check_xinjiang.py

# 4. 重新构建前端
cd ../fronted && npm run build

# 5. 重启服务并刷新浏览器
```

执行完这些步骤后，新疆应该能正常显示了！ 🎉

---

**快速命令（一次性执行）**：
```bash
cd d:\workspace\botnet\backend && python fix_region_names.py && cd ..\fronted && npm run build
```
