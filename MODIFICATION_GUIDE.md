# 双平台修改指南

## ? 你的4个URL需要改造

| # | 原始URL（?不安全） |
|---|-------------------|
| 1 | `http://10.61.241.38:9000/login?username=admin&password=123456&menu=server` |
| 2 | `http://10.61.241.38:9000/login?username=admin&password=123456&menu=clear#/login` |
| 3 | `http://10.61.241.38:9000/login?username=admin&password=123456&menu=node_distribution#/login` |
| 4 | `http://10.61.241.38:9000/login?username=op1&password=123456#/login` |

**问题**：密码明文显示在URL中

**目标**：改成token形式，如 `http://10.61.241.38:9000/login?token=xB3mK9p...&menu=server`

---

## ? 本平台（http://10.61.241.38:9000）：无需修改

### 已完成的工作

| 功能 | 状态 | 说明 |
|------|------|------|
| 后端支持token登录 | ? 完成 | `/api/user/auto-login?token=xxx` |
| 前端检测token参数 | ? 完成 | 自动检测URL中的token |
| Token生成接口 | ? 完成 | POST `/api/user/generate-login-token` |
| 生成链接接口 | ? 完成 | GET `/api/user/generate-login-link` |
| 重定向服务 | ? 完成 | GET `/api/user/legacy-login-redirect` |

**结论**：本平台已经100%准备就绪，**无需任何修改**！

---

## ? 调用平台：需要修改代码

### 核心改动

**原理**：调用平台在跳转前，先调用本平台的接口生成token，然后用token构建URL。

### 代码对比

#### ? 旧代码（不安全）

```python
# 调用平台原来的代码
import webbrowser

# 直接构建URL，密码暴露
url = "http://10.61.241.38:9000/login?username=admin&password=123456&menu=server"
webbrowser.open(url)
```

#### ? 新代码（安全）- 方案1（推荐）

```python
# 调用平台修改后的代码
import requests
import webbrowser

def jump_to_platform(username, password, menu=None, hash_fragment=None):
    """跳转到目标平台（安全方式）"""
    
    # 步骤1: 调用目标平台接口生成安全链接
    params = {'username': username, 'password': password}
    if menu:
        params['menu'] = menu
    
    response = requests.get(
        'http://10.61.241.38:8000/api/user/generate-login-link',
        params=params
    )
    
    if response.status_code == 200:
        safe_url = response.json()['login_url']
        
        # 步骤2: 添加hash片段（如果需要）
        if hash_fragment:
            safe_url += hash_fragment
        
        # 步骤3: 跳转（URL中不含密码）
        webbrowser.open(safe_url)
        return True
    
    return False

# 使用示例
jump_to_platform('admin', '123456', menu='server')
jump_to_platform('admin', '123456', menu='clear', hash_fragment='#/login')
jump_to_platform('admin', '123456', menu='node_distribution', hash_fragment='#/login')
jump_to_platform('op1', '123456', hash_fragment='#/login')
```

---

## ? 调用平台具体修改步骤

### 步骤1: 找到原来的跳转代码

在调用平台项目中，找到类似这样的代码：

```python
# 可能的位置：
# - 某个按钮点击事件
# - 某个跳转函数
# - 某个URL生成函数

url = f"http://10.61.241.38:9000/login?username={username}&password={password}&menu={menu}"
# 跳转逻辑（webbrowser.open / window.location.href / 等）
```

### 步骤2: 添加helper函数

在调用平台项目中添加这个函数：

```python
import requests

def generate_safe_login_url(username, password, menu=None, hash_fragment=None):
    """
    生成安全的登录URL
    
    调用目标平台接口，获取包含token的安全URL
    """
    params = {'username': username, 'password': password}
    if menu:
        params['menu'] = menu
    
    try:
        response = requests.get(
            'http://10.61.241.38:8000/api/user/generate-login-link',
            params=params,
            timeout=10
        )
        
        if response.status_code == 200:
            safe_url = response.json()['login_url']
            
            if hash_fragment:
                safe_url += hash_fragment
            
            return safe_url
        else:
            # 错误处理
            print(f"生成链接失败: {response.text}")
            return None
    except Exception as e:
        print(f"请求失败: {e}")
        return None
```

### 步骤3: 修改跳转逻辑

将原来的代码：

```python
# 旧代码
url = f"http://10.61.241.38:9000/login?username={username}&password={password}&menu={menu}"
webbrowser.open(url)
```

改为：

```python
# 新代码
safe_url = generate_safe_login_url(username, password, menu=menu, hash_fragment='#/login')
if safe_url:
    webbrowser.open(safe_url)
else:
    # 错误处理
    print("无法生成安全URL")
```

### 步骤4: 测试

测试所有跳转场景：

```python
# 测试1
generate_safe_login_url('admin', '123456', menu='server')

# 测试2
generate_safe_login_url('admin', '123456', menu='clear', hash_fragment='#/login')

# 测试3
generate_safe_login_url('admin', '123456', menu='node_distribution', hash_fragment='#/login')

# 测试4
generate_safe_login_url('op1', '123456', hash_fragment='#/login')
```

---

## ? 不同语言的实现

### Python

```python
import requests
import webbrowser

def jump_to_platform(username, password, menu=None, hash_fragment=None):
    params = {'username': username, 'password': password}
    if menu:
        params['menu'] = menu
    
    r = requests.get('http://10.61.241.38:8000/api/user/generate-login-link', params=params)
    if r.status_code == 200:
        url = r.json()['login_url']
        if hash_fragment:
            url += hash_fragment
        webbrowser.open(url)
```

### JavaScript

```javascript
async function jumpToPlatform(username, password, menu = null, hashFragment = null) {
    const params = new URLSearchParams({username, password});
    if (menu) params.append('menu', menu);
    
    const response = await fetch(
        `http://10.61.241.38:8000/api/user/generate-login-link?${params}`
    );
    
    if (response.ok) {
        const data = await response.json();
        let url = data.login_url;
        if (hashFragment) url += hashFragment;
        window.location.href = url;
    }
}

// 使用
jumpToPlatform('admin', '123456', 'server');
jumpToPlatform('admin', '123456', 'clear', '#/login');
```

### Java

```java
import java.net.http.*;
import java.net.URI;
import org.json.JSONObject;

public class PlatformJumper {
    public static String generateSafeUrl(String username, String password, String menu, String hashFragment) {
        try {
            String url = String.format(
                "http://10.61.241.38:8000/api/user/generate-login-link?username=%s&password=%s",
                username, password
            );
            
            if (menu != null) {
                url += "&menu=" + menu;
            }
            
            HttpClient client = HttpClient.newHttpClient();
            HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(url))
                .GET()
                .build();
            
            HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
            
            if (response.statusCode() == 200) {
                JSONObject data = new JSONObject(response.body());
                String safeUrl = data.getString("login_url");
                
                if (hashFragment != null) {
                    safeUrl += hashFragment;
                }
                
                return safeUrl;
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
        return null;
    }
}
```

---

## ? 修改工作量评估

| 平台 | 需要修改 | 工作量 | 时间估计 |
|------|---------|--------|----------|
| 本平台 | ? 不需要 | 0 | 0分钟 |
| 调用平台 | ? 需要 | 低 | 30-60分钟 |

### 调用平台修改清单

- [ ] 1. 添加helper函数 `generate_safe_login_url()` （10分钟）
- [ ] 2. 修改跳转逻辑（4处） （20分钟）
- [ ] 3. 测试所有场景 （20分钟）
- [ ] 4. 部署上线 （10分钟）

**总计**：约60分钟

---

## ? 测试验证

### 使用转换工具

```bash
# 运行转换工具，查看效果
cd /home/spider/31339752
python3 convert_urls_to_token.py
```

这个工具会：
1. 展示如何转换你的4个URL
2. 提供调用平台代码示例
3. 对比三种方案

### 手动测试

```bash
# 测试生成链接接口
curl "http://10.61.241.38:8000/api/user/generate-login-link?username=admin&password=123456&menu=server"

# 预期返回：
# {
#   "token": "xB3mK9pL...",
#   "login_url": "http://10.61.241.38:9000/login?token=xB3mK9pL...&menu=server",
#   "expires_at": "2026-04-22 17:30:00",
#   "expires_in_seconds": 300,
#   "menu": "server"
# }
```

---

## ? 快速开始（临时方案）

如果调用平台暂时无法修改代码，可以使用重定向服务：

### 最小修改方案

只需修改URL路径：

```python
# 旧URL
old_url = "http://10.61.241.38:9000/login?username=admin&password=123456&menu=server"

# 新URL（只改了域名和路径）
new_url = "http://10.61.241.38:8000/api/user/legacy-login-redirect?username=admin&password=123456&menu=server"

webbrowser.open(new_url)
# 浏览器会自动重定向到安全URL
```

**优势**：改动最小，5分钟搞定  
**劣势**：仍在服务端接收明文密码，建议作为临时方案

---

## ? 支持资源

- **转换工具**: `convert_urls_to_token.py`
- **给调用平台的文档**: `docs/FOR_EXTERNAL_PLATFORM.md`
- **快速参考**: `TOKEN_LOGIN_QUICK_REFERENCE.md`
- **API文档**: http://10.61.241.38:8000/docs

---

## ? 检查清单

### 本平台
- [x] 后端支持token登录
- [x] 前端检测token参数
- [x] Token生成接口
- [x] 生成链接接口
- [x] 重定向服务
- [x] 文档和工具

### 调用平台（待完成）
- [ ] 添加helper函数
- [ ] 修改URL 1的跳转逻辑
- [ ] 修改URL 2的跳转逻辑
- [ ] 修改URL 3的跳转逻辑
- [ ] 修改URL 4的跳转逻辑
- [ ] 测试所有场景
- [ ] 部署上线

---

## ? 总结

| 项目 | 状态 |
|------|------|
| **本平台** | ? 100%完成，无需修改 |
| **调用平台** | ? 需要修改，约60分钟工作量 |
| **修改难度** | ?? (简单) |
| **推荐方案** | 方案1：使用生成链接接口 |

**下一步**：运行 `python3 convert_urls_to_token.py` 查看演示
