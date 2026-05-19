# URL转换示例 - 从明文密码到Token方式

## 📋 你的四个URL转换对照

### URL 1: 服务器管理页面

**旧URL（不安全❌）**:
```
http://10.61.241.38:9000/login?username=admin&password=123456&menu=server
```

**新URL（安全✅）** - 示例:
```
http://10.61.241.38:9000/login?token=xB3mK9pL2qR8vN4hS7tY1zW6cF5jD0aE9gH4iM3nO2pQ1rT8uV&menu=server
```

---

### URL 2: 清除页面

**旧URL（不安全❌）**:
```
http://10.61.241.38:9000/login?username=admin&password=123456&menu=clear#/login
```

**新URL（安全✅）** - 示例:
```
http://10.61.241.38:9000/login?token=yC4nL0qM3rS9wO5iT8zX2aG7dH6kE1bF0hJ5nN4oP3qR2sU9vW&menu=clear#/login
```

---

### URL 3: 节点分布页面

**旧URL（不安全❌）**:
```
http://10.61.241.38:9000/login?username=admin&password=123456&menu=node_distribution#/login
```

**新URL（安全✅）** - 示例:
```
http://10.61.241.38:9000/login?token=zA5oM1pN4sT0xP6jU9aY3bH8eI7lF2cG1iK6oO5pQ4rS3tV0wX&menu=node_distribution#/login
```

---

### URL 4: 操作员登录

**旧URL（不安全❌）**:
```
http://10.61.241.38:9000/login?username=op1&password=123456#/login
```

**新URL（安全✅）** - 示例:
```
http://10.61.241.38:9000/login?token=aB6pN2qO5tU1yQ7kV0bZ4cI9fJ8mG3dH2jL7pP6qR5sT4uW1xY#/login
```

---

## 💻 其他平台代码修改示例

### 方法1: 使用生成链接接口（推荐⭐⭐⭐⭐⭐）

#### Python代码

```python
import requests
import webbrowser

def create_safe_login_url(username, password, menu=None, hash_fragment=None):
    """
    生成安全的登录URL
    
    Args:
        username: 用户名
        password: 密码
        menu: 菜单参数（可选）
        hash_fragment: URL片段（可选，如 '/login'）
    
    Returns:
        安全的token URL
    """
    # 准备参数
    params = {
        'username': username,
        'password': password,
        'frontend_url': 'http://10.10.66.95.83'
    }
    
    if menu:
        params['menu'] = menu
    
    # 调用接口生成安全链接
    response = requests.get(
        'http://10.61.241.38:8000/api/user/generate-login-link',
        params=params
    )
    
    if response.status_code == 200:
        data = response.json()
        safe_url = data['login_url']
        
        # 添加hash fragment（如果有）
        if hash_fragment:
            safe_url += f"#{hash_fragment}"
        
        return safe_url
    else:
        raise Exception(f"生成URL失败: {response.text}")

# === 使用示例 ===

# 示例1: 服务器管理页面
url1 = create_safe_login_url('admin', '123456', menu='server')
print(f"URL1: {url1}")
# webbrowser.open(url1)

# 示例2: 清除页面（带hash）
url2 = create_safe_login_url('admin', '123456', menu='clear', hash_fragment='/login')
print(f"URL2: {url2}")
# webbrowser.open(url2)

# 示例3: 节点分布页面（带hash）
url3 = create_safe_login_url('admin', '123456', menu='node_distribution', hash_fragment='/login')
print(f"URL3: {url3}")
# webbrowser.open(url3)

# 示例4: 操作员登录（带hash）
url4 = create_safe_login_url('op1', '123456', hash_fragment='/login')
print(f"URL4: {url4}")
# webbrowser.open(url4)
```

#### JavaScript代码

```javascript
/**
 * 生成安全的登录URL
 */
async function createSafeLoginUrl(username, password, menu = null, hashFragment = null) {
    // 准备参数
    const params = new URLSearchParams({
        username: username,
        password: password,
        frontend_url: 'http://10.10.66.95.83'
    });
    
    if (menu) {
        params.append('menu', menu);
    }
    
    // 调用接口
    const response = await fetch(
        `http://10.61.241.38:8000/api/user/generate-login-link?${params}`
    );
    
    if (response.ok) {
        const data = await response.json();
        let safeUrl = data.login_url;
        
        // 添加hash fragment
        if (hashFragment) {
            safeUrl += `#${hashFragment}`;
        }
        
        return safeUrl;
    } else {
        throw new Error(`生成URL失败: ${await response.text()}`);
    }
}

// === 使用示例 ===

// 示例1: 服务器管理页面
const url1 = await createSafeLoginUrl('admin', '123456', 'server');
console.log('URL1:', url1);
// window.location.href = url1;

// 示例2: 清除页面（带hash）
const url2 = await createSafeLoginUrl('admin', '123456', 'clear', '/login');
console.log('URL2:', url2);

// 示例3: 节点分布页面（带hash）
const url3 = await createSafeLoginUrl('admin', '123456', 'node_distribution', '/login');
console.log('URL3:', url3);

// 示例4: 操作员登录（带hash）
const url4 = await createSafeLoginUrl('op1', '123456', null, '/login');
console.log('URL4:', url4);
```

---

### 方法2: 使用重定向服务（临时方案）

#### Python代码

```python
import webbrowser

# 只需修改URL路径，其他不变

# 示例1: 服务器管理页面
url1 = "http://10.61.241.38:8000/api/user/legacy-login-redirect?username=admin&password=123456&menu=server"
webbrowser.open(url1)  # 会自动重定向到token URL

# 示例2: 清除页面
url2 = "http://10.61.241.38:8000/api/user/legacy-login-redirect?username=admin&password=123456&menu=clear#/login"
webbrowser.open(url2)

# 示例3: 节点分布页面
url3 = "http://10.61.241.38:8000/api/user/legacy-login-redirect?username=admin&password=123456&menu=node_distribution#/login"
webbrowser.open(url3)

# 示例4: 操作员登录
url4 = "http://10.61.241.38:8000/api/user/legacy-login-redirect?username=op1&password=123456#/login"
webbrowser.open(url4)
```

---

## 🔧 批量转换工具

使用我们提供的转换脚本：

```bash
cd /home/spider/31339752

# 转换你的四个URL
python3 convert_urls_to_token.py
```

这个脚本会：
1. 自动调用token生成接口
2. 转换所有URL
3. 显示转换结果
4. 保存到 `converted_urls.json` 文件

---

## 📊 对比总结

| URL编号 | 用户 | 菜单 | Hash | 旧方式安全性 | 新方式安全性 |
|---------|------|------|------|--------------|--------------|
| 1 | admin | server | 无 | ❌ 密码明文 | ✅ Token |
| 2 | admin | clear | /login | ❌ 密码明文 | ✅ Token |
| 3 | admin | node_distribution | /login | ❌ 密码明文 | ✅ Token |
| 4 | op1 | 无 | /login | ❌ 密码明文 | ✅ Token |

---

## ✅ 实施步骤

### 步骤1: 确认后端服务运行
```bash
curl http://10.61.241.38:8000/api/upload-status
```

### 步骤2: 测试生成链接接口
```bash
curl "http://10.61.241.38:8000/api/user/generate-login-link?username=admin&password=123456&menu=server"
```

### 步骤3: 使用转换工具
```bash
python3 convert_urls_to_token.py
```

### 步骤4: 在其他平台应用新代码
将上面的代码示例应用到其他平台的跳转逻辑中。

### 步骤5: 验证
在浏览器中打开生成的URL，检查：
- 地址栏不显示密码 ✅
- 自动登录成功 ✅
- 菜单参数正确 ✅
- Hash fragment正确 ✅

---

## 🎯 关键点

1. **Token是实时生成的**：每次跳转时调用接口生成新token
2. **Token有效期5分钟**：足够用户完成跳转
3. **Token只能用一次**：使用后立即失效
4. **支持所有参数**：menu、hash fragment都支持

---

## 💡 建议

**短期（今天）**：
- 使用方法2（重定向服务），快速解决安全问题

**中期（本周）**：
- 迁移到方法1（生成链接接口）

**长期**：
- 考虑在其他平台缓存用户凭证，避免每次都传密码
