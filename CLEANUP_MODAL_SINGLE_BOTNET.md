# 一键清除模态框 - 单僵网显示功能

## 📋 需求

**修改前**：点击一键清除后，模态框显示所有僵网的信息  
**修改后**：只显示当前选中僵网的信息，并对该僵网进行清除操作

## 🔧 实现方案

### 1. Takeover.js 修改

**传递 `selectedNetwork` 参数给 CleanupModal**

```jsx
{showCleanupModal && (
  <CleanupModal 
    onClose={() => setShowCleanupModal(false)} 
    dispatch={dispatch}
    selectedNetwork={selectedNetwork}  // ✅ 新增：传递当前选中的僵网
  />
)}
```

### 2. CleanupModal.js 修改

#### 2.1 接收 `selectedNetwork` 参数

```jsx
const CleanupModal = ({ onClose, dispatch, selectedNetwork }) => {
  // ...
}
```

#### 2.2 过滤僵网列表

```jsx
const fetchBotnets = async () => {
  // ...
  if (response.data.status === 'success') {
    const allBotnets = response.data.data.botnets || [];
    // 如果有选中的僵网，只显示该僵网；否则显示所有僵网
    if (selectedNetwork) {
      const filteredBotnets = allBotnets.filter(b => b.botnet_name === selectedNetwork);
      setBotnets(filteredBotnets);
    } else {
      setBotnets(allBotnets);
    }
  }
}
```

#### 2.3 更新依赖项

```jsx
useEffect(() => {
  fetchBotnets();
}, [selectedNetwork]);  // ✅ 当selectedNetwork变化时重新获取
```

#### 2.4 优化标题显示

```jsx
<ModalTitle>
  <span className="icon">🎯</span>
  <span>
    {selectedNetwork ? 
      (botnets.length > 0 ? 
        `${botnets[0].display_name || selectedNetwork} - 一键清除` : 
        `${selectedNetwork} - 一键清除`) : 
      '僵网一键清除'
    }
  </span>
  {/* 只在显示所有僵网时显示统计徽章 */}
  {!loading && !selectedNetwork && (
    <>
      <span className="count-badge">有权限: {withPermission}</span>
      {withoutPermission > 0 && (
        <span className="warning-badge">无权限: {withoutPermission}</span>
      )}
    </>
  )}
</ModalTitle>
```

#### 2.5 优化空数据提示

```jsx
{botnets.length === 0 ? (
  <EmptyMessage>
    {selectedNetwork ? 
      `未找到僵网 "${selectedNetwork}" 的清除配置信息` : 
      '暂无僵网数据'
    }
  </EmptyMessage>
) : (
  // 渲染僵网卡片
)}
```

## 🎨 用户体验改进

### 显示逻辑

| 场景 | 标题 | 内容 |
|------|------|------|
| 选中 ramnit 僵网 | "Ramnit僵尸网络 - 一键清除" | 只显示 ramnit 的清除卡片 |
| 选中 utg_q_008 僵网 | "UTG-q-008僵尸网络 - 一键清除" | 只显示 utg_q_008 的清除卡片 |
| 未选中任何僵网 | "僵网一键清除" | 显示所有僵网（保持兼容） |

### 错误处理

- ✅ 如果选中的僵网不在清除配置中，显示友好提示
- ✅ 加载状态正确显示
- ✅ 空数据状态有明确说明

## 📊 测试场景

### 测试1：选中单个僵网
1. 在页面上选择 "ramnit" 僵网
2. 点击 "一键清除" 按钮
3. **预期结果**：
   - 模态框标题显示 "Ramnit僵尸网络 - 一键清除"
   - 只显示 ramnit 的清除卡片
   - 可以对 ramnit 执行查询/清除/重置操作

### 测试2：选中 utg_q_008
1. 在页面上选择 "utg_q_008" 僵网
2. 点击 "一键清除" 按钮
3. **预期结果**：
   - 模态框标题显示 "UTG-q-008僵尸网络 - 一键清除"
   - 只显示 utg_q_008 的清除卡片
   - 显示 C2 IP: 43.99.37.118

### 测试3：未配置清除的僵网
1. 在页面上选择一个没有配置 C2 清除的僵网（如 mozi）
2. 点击 "一键清除" 按钮
3. **预期结果**：
   - 模态框标题显示僵网名称
   - 显示该僵网的卡片，但操作按钮禁用
   - 显示原因："未配置C2服务器" 或 "未配置操作接口"

### 测试4：切换僵网
1. 打开清除模态框（显示僵网A）
2. 关闭模态框
3. 切换到僵网B
4. 再次打开清除模态框
5. **预期结果**：
   - 模态框显示僵网B的信息（而不是僵网A）

## 🚀 部署说明

### 修改的文件

1. **fronted/src/components/centerPage/charts/Takeover.js**
   - 传递 `selectedNetwork` 参数

2. **fronted/src/components/CleanupModal.js**
   - 接收并使用 `selectedNetwork` 参数
   - 过滤僵网列表
   - 优化UI显示

### 部署步骤

1. 保存所有修改的文件
2. 重启前端开发服务器（如果正在运行）
3. 刷新浏览器页面
4. 按照上述测试场景验证功能

## ✅ 优势

1. **更聚焦**：用户只看到当前关心的僵网，避免信息过载
2. **更安全**：减少误操作其他僵网的可能性
3. **更快速**：不需要在列表中寻找目标僵网
4. **保持兼容**：如果没有选中僵网，仍然显示所有僵网（可用于管理场景）

---

**修改日期**: 2026-03-07  
**状态**: ✅ 完成
