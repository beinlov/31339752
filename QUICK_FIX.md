# ⚡ 快速修复指南

## 🔴 问题：拉取不到数据

### 症状
- 日志处理器显示：`远程拉取: 总计 0, 已保存 0`
- Worker没有任务
- 前端无数据

---

## ✅ 一键修复（推荐）

```bash
# 方法1：运行自动修复脚本
cd d:\workspace\botnet
fix_pull_issue_auto.bat

# 方法2：手动重置
cd d:\workspace\botnet\backend
del .remote_puller_state.json
```

**然后重启日志处理器：**
```bash
# 关闭旧的"Botnet Log Processor"窗口
# 重新启动：
cd d:\workspace\botnet\backend
python log_processor/main.py
```

---

## 📊 验证修复

**60秒后查看日志，应该看到：**
```
[C2-test-local] 拉取全部数据（无断点续传）
[C2-test-local] 拉取成功: 1000 条
[test] 已推送 1000 条数据到队列
```

---

## 🎯 根本原因

**断点续传时间戳问题：**
- 状态文件记录：`since=2026-01-08T09:59:59`
- C2端查询：`WHERE timestamp > '2026-01-08 09:59:59'`
- 结果：如果没有更新的数据，返回0条

**解决方案：**
- 删除状态文件
- 不使用since参数
- 拉取全部数据

---

## 🔧 永久修复

**已修改代码，自动处理：**
- ✅ 检测到0条返回时，自动清除时间戳
- ✅ 下次自动拉取全部数据
- ✅ 无需手动干预

**修改文件：**
- `backend/log_processor/remote_puller.py`

---

## 🚀 完成

修复后，系统应该正常运行：
1. ✅ 拉取数据正常
2. ✅ Worker处理快速（~3秒/1000条）
3. ✅ 前端显示数据

---

**如果还有问题，查看：** `解决方案-拉取不到数据.md`
