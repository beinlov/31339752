# 第三方集成平台用户管理API使用指南

## 概述

本文档专为第三方集成平台提供用户名密码的增删改查操作API接口。接口设计简洁，专注于核心功能，便于第三方系统快速集成。

## 核心功能

- ✅ **获取用户列表** - 获取所有用户名
- ✅ **检查用户存在** - 验证用户名是否存在
- ✅ **创建用户** - 用户名+密码创建
- ✅ **更新密码** - 修改用户密码
- ✅ **删除用户** - 删除指定用户
- ✅ **简化认证** - 仅需API密钥

## 基础信息

- **基础URL**: `http://your-domain:port/api/integration`
- **认证方式**: API密钥 (X-API-Key)
- **数据格式**: JSON
- **字符编码**: UTF-8

## 快速开始

### 1. 配置API密钥

在服务端 `integration_platform_api.py` 中修改：

```python
# 集成平台API密钥配置（生产环境必须修改）
INTEGRATION_API_KEY = "YOUR_SECURE_API_KEY_HERE"
```

### 2. 基本请求格式

所有请求都需要在请求头中包含API密钥：

```
X-API-Key: YOUR_SECURE_API_KEY_HERE
Content-Type: application/json
```

## API接口详情

### 1. 获取用户列表

**接口**: `GET /api/integration/users`

**描述**: 获取系统中所有用户的用户名列表

**请求头**:
```
X-API-Key: YOUR_SECURE_API_KEY_HERE
```

**响应示例**:
```json
{
    "success": true,
    "users": ["admin", "user1", "user2", "test_user"],
    "total": 4
}
```

**cURL示例**:
```bash
curl -X GET "http://localhost:9000/api/integration/users" \
  -H "X-API-Key: YOUR_SECURE_API_KEY_HERE"
```

### 2. 检查用户是否存在

**接口**: `GET /api/integration/users/{username}`

**描述**: 检查指定用户名是否存在于系统中

**请求头**:
```
X-API-Key: YOUR_SECURE_API_KEY_HERE
```

**响应示例**:
```json
{
    "success": true,
    "message": "用户 test_user 存在",
    "data": {
        "username": "test_user",
        "exists": true
    }
}
```

**cURL示例**:
```bash
curl -X GET "http://localhost:9000/api/integration/users/test_user" \
  -H "X-API-Key: YOUR_SECURE_API_KEY_HERE"
```

### 3. 创建用户

**接口**: `POST /api/integration/users`

**描述**: 创建新用户（用户名+密码），默认角色为"访客"，状态为"离线"

**请求头**:
```
X-API-Key: YOUR_SECURE_API_KEY_HERE
Content-Type: application/json
```

**请求体**:
```json
{
    "username": "new_user",
    "password": "password123"
}
```

**响应示例**:
```json
{
    "success": true,
    "message": "用户 new_user 创建成功",
    "data": {
        "user_id": 10,
        "username": "new_user"
    }
}
```

**cURL示例**:
```bash
curl -X POST "http://localhost:9000/api/integration/users" \
  -H "X-API-Key: YOUR_SECURE_API_KEY_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "new_user",
    "password": "password123"
  }'
```

### 4. 更新用户密码

**接口**: `PUT /api/integration/users/{username}`

**描述**: 更新指定用户的密码（不能修改admin用户密码）

**请求头**:
```
X-API-Key: YOUR_SECURE_API_KEY_HERE
Content-Type: application/json
```

**请求体**:
```json
{
    "password": "new_password123"
}
```

**响应示例**:
```json
{
    "success": true,
    "message": "用户 test_user 密码更新成功",
    "data": {
        "username": "test_user"
    }
}
```

**cURL示例**:
```bash
curl -X PUT "http://localhost:9000/api/integration/users/test_user" \
  -H "X-API-Key: YOUR_SECURE_API_KEY_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "password": "new_password123"
  }'
```

### 5. 删除用户

**接口**: `DELETE /api/integration/users/{username}`

**描述**: 删除指定用户（不能删除admin用户）

**请求头**:
```
X-API-Key: YOUR_SECURE_API_KEY_HERE
```

**响应示例**:
```json
{
    "success": true,
    "message": "用户 test_user 删除成功",
    "data": {
        "username": "test_user"
    }
}
```

**cURL示例**:
```bash
curl -X DELETE "http://localhost:9000/api/integration/users/test_user" \
  -H "X-API-Key: YOUR_SECURE_API_KEY_HERE"
```

### 6. 获取接口配置

**接口**: `GET /api/integration/config`

**描述**: 获取API接口配置信息，无需认证

**响应示例**:
```json
{
    "api_version": "1.0",
    "description": "第三方集成平台用户管理API - 专注于用户名密码的增删改查操作",
    "authentication": {
        "type": "API Key",
        "header": "X-API-Key",
        "required": true
    },
    "endpoints": {
        "get_users": {
            "method": "GET",
            "path": "/api/integration/users",
            "description": "获取所有用户名列表"
        },
        "check_user": {
            "method": "GET",
            "path": "/api/integration/users/{username}",
            "description": "检查用户是否存在"
        },
        "create_user": {
            "method": "POST",
            "path": "/api/integration/users",
            "description": "创建新用户（用户名+密码）"
        },
        "update_password": {
            "method": "PUT",
            "path": "/api/integration/users/{username}",
            "description": "更新用户密码"
        },
        "delete_user": {
            "method": "DELETE",
            "path": "/api/integration/users/{username}",
            "description": "删除用户"
        }
    },
    "security": {
        "api_key_enabled": true,
        "ip_whitelist_enabled": false,
        "protected_users": ["admin"]
    },
    "user_defaults": {
        "role": "访客",
        "status": "离线"
    }
}
```

## 错误处理

### 常见错误码

- `400`: 请求参数错误（如用户名已存在、密码太短等）
- `401`: API密钥无效或缺失
- `403`: IP地址不在白名单中（如果启用IP白名单）
- `404`: 用户不存在
- `500`: 服务器内部错误

### 错误响应格式

```json
{
    "detail": "具体错误描述信息"
}
```

### 常见错误示例

**API密钥缺失**:
```json
{
    "detail": "缺少API密钥，请在请求头中添加 X-API-Key"
}
```

**用户名已存在**:
```json
{
    "detail": "用户名已存在"
}
```

**用户不存在**:
```json
{
    "detail": "用户不存在"
}
```

**不能操作admin用户**:
```json
{
    "detail": "不能修改admin用户密码"
}
```

## 编程语言示例

### Python示例

```python
import requests
import json

class ThirdPartyUserAPI:
    def __init__(self, base_url, api_key):
        self.base_url = base_url
        self.api_key = api_key
        self.headers = {
            "X-API-Key": api_key,
            "Content-Type": "application/json"
        }
    
    def get_users(self):
        """获取所有用户名列表"""
        response = requests.get(f"{self.base_url}/users", headers=self.headers)
        return response.json()
    
    def check_user_exists(self, username):
        """检查用户是否存在"""
        response = requests.get(f"{self.base_url}/users/{username}", headers=self.headers)
        return response.json()
    
    def create_user(self, username, password):
        """创建新用户"""
        data = {"username": username, "password": password}
        response = requests.post(f"{self.base_url}/users", headers=self.headers, json=data)
        return response.json()
    
    def update_password(self, username, new_password):
        """更新用户密码"""
        data = {"password": new_password}
        response = requests.put(f"{self.base_url}/users/{username}", headers=self.headers, json=data)
        return response.json()
    
    def delete_user(self, username):
        """删除用户"""
        response = requests.delete(f"{self.base_url}/users/{username}", headers=self.headers)
        return response.json()

# 使用示例
if __name__ == "__main__":
    api = ThirdPartyUserAPI(
        base_url="http://localhost:9000/api/integration",
        api_key="YOUR_SECURE_API_KEY_HERE"
    )
    
    # 获取用户列表
    users = api.get_users()
    print(f"系统中有 {users['total']} 个用户: {users['users']}")
    
    # 检查用户是否存在
    check_result = api.check_user_exists("test_user")
    print(f"用户检查结果: {check_result['message']}")
    
    # 创建用户
    if not check_result['data']['exists']:
        create_result = api.create_user("test_user", "password123")
        if create_result['success']:
            print(f"用户创建成功: {create_result['message']}")
            
            # 更新密码
            update_result = api.update_password("test_user", "new_password456")
            print(f"密码更新结果: {update_result['message']}")
            
            # 删除用户
            delete_result = api.delete_user("test_user")
            print(f"用户删除结果: {delete_result['message']}")
```

### JavaScript示例

```javascript
class ThirdPartyUserAPI {
    constructor(baseUrl, apiKey) {
        this.baseUrl = baseUrl;
        this.apiKey = apiKey;
        this.headers = {
            'X-API-Key': apiKey,
            'Content-Type': 'application/json'
        };
    }
    
    async getUsers() {
        const response = await fetch(`${this.baseUrl}/users`, {
            method: 'GET',
            headers: this.headers
        });
        return await response.json();
    }
    
    async checkUserExists(username) {
        const response = await fetch(`${this.baseUrl}/users/${username}`, {
            method: 'GET',
            headers: this.headers
        });
        return await response.json();
    }
    
    async createUser(username, password) {
        const response = await fetch(`${this.baseUrl}/users`, {
            method: 'POST',
            headers: this.headers,
            body: JSON.stringify({ username, password })
        });
        return await response.json();
    }
    
    async updatePassword(username, newPassword) {
        const response = await fetch(`${this.baseUrl}/users/${username}`, {
            method: 'PUT',
            headers: this.headers,
            body: JSON.stringify({ password: newPassword })
        });
        return await response.json();
    }
    
    async deleteUser(username) {
        const response = await fetch(`${this.baseUrl}/users/${username}`, {
            method: 'DELETE',
            headers: this.headers
        });
        return await response.json();
    }
}

// 使用示例
(async () => {
    const api = new ThirdPartyUserAPI(
        'http://localhost:9000/api/integration',
        'YOUR_SECURE_API_KEY_HERE'
    );
    
    try {
        // 获取用户列表
        const users = await api.getUsers();
        console.log(`系统中有 ${users.total} 个用户:`, users.users);
        
        // 检查用户是否存在
        const checkResult = await api.checkUserExists('test_user');
        console.log('用户检查结果:', checkResult.message);
        
        // 创建用户
        if (!checkResult.data.exists) {
            const createResult = await api.createUser('test_user', 'password123');
            console.log('用户创建结果:', createResult.message);
            
            // 更新密码
            const updateResult = await api.updatePassword('test_user', 'new_password456');
            console.log('密码更新结果:', updateResult.message);
            
            // 删除用户
            const deleteResult = await api.deleteUser('test_user');
            console.log('用户删除结果:', deleteResult.message);
        }
    } catch (error) {
        console.error('API调用失败:', error);
    }
})();
```

### Java示例

```java
import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.JsonNode;

public class ThirdPartyUserAPI {
    private final String baseUrl;
    private final String apiKey;
    private final HttpClient client;
    private final ObjectMapper mapper;
    
    public ThirdPartyUserAPI(String baseUrl, String apiKey) {
        this.baseUrl = baseUrl;
        this.apiKey = apiKey;
        this.client = HttpClient.newHttpClient();
        this.mapper = new ObjectMapper();
    }
    
    public JsonNode getUsers() throws IOException, InterruptedException {
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(baseUrl + "/users"))
            .header("X-API-Key", apiKey)
            .GET()
            .build();
        
        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
        return mapper.readTree(response.body());
    }
    
    public JsonNode createUser(String username, String password) throws IOException, InterruptedException {
        String json = String.format("{\"username\":\"%s\",\"password\":\"%s\"}", username, password);
        
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(baseUrl + "/users"))
            .header("X-API-Key", apiKey)
            .header("Content-Type", "application/json")
            .POST(HttpRequest.BodyPublishers.ofString(json))
            .build();
        
        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
        return mapper.readTree(response.body());
    }
    
    public JsonNode updatePassword(String username, String newPassword) throws IOException, InterruptedException {
        String json = String.format("{\"password\":\"%s\"}", newPassword);
        
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(baseUrl + "/users/" + username))
            .header("X-API-Key", apiKey)
            .header("Content-Type", "application/json")
            .PUT(HttpRequest.BodyPublishers.ofString(json))
            .build();
        
        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
        return mapper.readTree(response.body());
    }
    
    public JsonNode deleteUser(String username) throws IOException, InterruptedException {
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(baseUrl + "/users/" + username))
            .header("X-API-Key", apiKey)
            .DELETE()
            .build();
        
        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
        return mapper.readTree(response.body());
    }
}
```

## 数据库表结构

### users表结构

```sql
CREATE TABLE `users` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `username` varchar(50) NOT NULL UNIQUE,
  `password` varchar(255) NOT NULL,
  `role` varchar(20) NOT NULL DEFAULT '访客',
  `status` varchar(20) DEFAULT '离线',
  `last_login` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

## 安全注意事项

1. **API密钥安全**: 
   - 生产环境必须修改默认API密钥
   - 不要在代码中硬编码API密钥
   - 定期更换API密钥

2. **IP白名单**:
   - 生产环境建议启用IP白名单
   - 只允许可信的IP地址访问

3. **用户权限**:
   - admin用户受到特殊保护，不能修改或删除
   - 新创建的用户默认为"访客"角色

4. **密码安全**:
   - 密码使用MD5哈希存储
   - 建议密码长度至少6位

## 测试工具

### Postman集合

可以导入以下Postman集合进行API测试：

```json
{
    "info": {
        "name": "第三方集成平台用户管理API",
        "description": "用于测试第三方集成平台用户管理API的Postman集合"
    },
    "variable": [
        {
            "key": "base_url",
            "value": "http://localhost:9000/api/integration"
        },
        {
            "key": "api_key",
            "value": "YOUR_SECURE_API_KEY_HERE"
        }
    ],
    "item": [
        {
            "name": "获取用户列表",
            "request": {
                "method": "GET",
                "header": [
                    {
                        "key": "X-API-Key",
                        "value": "{{api_key}}"
                    }
                ],
                "url": "{{base_url}}/users"
            }
        },
        {
            "name": "检查用户存在",
            "request": {
                "method": "GET",
                "header": [
                    {
                        "key": "X-API-Key",
                        "value": "{{api_key}}"
                    }
                ],
                "url": "{{base_url}}/users/test_user"
            }
        },
        {
            "name": "创建用户",
            "request": {
                "method": "POST",
                "header": [
                    {
                        "key": "X-API-Key",
                        "value": "{{api_key}}"
                    },
                    {
                        "key": "Content-Type",
                        "value": "application/json"
                    }
                ],
                "body": {
                    "mode": "raw",
                    "raw": "{\n    \"username\": \"test_user\",\n    \"password\": \"password123\"\n}"
                },
                "url": "{{base_url}}/users"
            }
        },
        {
            "name": "更新用户密码",
            "request": {
                "method": "PUT",
                "header": [
                    {
                        "key": "X-API-Key",
                        "value": "{{api_key}}"
                    },
                    {
                        "key": "Content-Type",
                        "value": "application/json"
                    }
                ],
                "body": {
                    "mode": "raw",
                    "raw": "{\n    \"password\": \"new_password456\"\n}"
                },
                "url": "{{base_url}}/users/test_user"
            }
        },
        {
            "name": "删除用户",
            "request": {
                "method": "DELETE",
                "header": [
                    {
                        "key": "X-API-Key",
                        "value": "{{api_key}}"
                    }
                ],
                "url": "{{base_url}}/users/test_user"
            }
        }
    ]
}
```

## 技术支持

如有问题，请：
1. 检查API密钥是否正确配置
2. 确认请求格式是否符合文档要求
3. 查看服务器日志获取详细错误信息
4. 联系技术支持团队

## 更新日志

- **v1.0** (2024-03-01): 初始版本，提供基础的用户名密码增删改查功能
