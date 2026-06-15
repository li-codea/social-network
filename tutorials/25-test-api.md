# 端到端 API 测试

> **源码文件**：`backend/test_api.py`

---

## 文件职责

对社交网络好友推荐系统的所有 API 端点进行端到端集成测试，共 12 个测试用例，覆盖用户 CRUD、好友关系管理、共同好友计算、好友推荐、错误处理等全部功能。

---

## 导入依赖

```python
import json
import urllib.request
import urllib.error
import urllib.parse
```

使用 Python 标准库的 `urllib` 发送 HTTP 请求（无第三方依赖），直接测试运行中的 API 服务。

---

## 模块级变量

```python
BASE = "http://localhost:8000/api/v1"
```

所有请求的基础 URL。测试前需确保后端服务已启动。

---

## 函数详解

### `request(method, path, body)` — HTTP 请求辅助函数

```python
def request(method, path, body=None):
    if "?" in path:
        base_path, query = path.split("?", 1)
        params = urllib.parse.parse_qs(query)
        encoded_params = urllib.parse.urlencode(params, doseq=True)
        path = f"{base_path}?{encoded_params}"
    url = BASE + urllib.parse.quote(path, safe="/?=&")
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `method` | `str` | HTTP 方法：`"GET"`, `"POST"`, `"PUT"`, `"DELETE"` |
| `path` | `str` | API 路径（如 `"/users/"`），自动拼接 `BASE` 前缀 |
| `body` | `dict` 或 `None` | JSON 请求体 |

**处理流程**：

1. **Query 参数编码**：如果路径中含 `?`，使用 `urllib.parse` 正确编码中文和特殊字符
2. **路径拼接**：`BASE + path`，并对 URL 进行安全引用编码
3. **请求体序列化**：将 `body` 字典 JSON 序列化后编码为字节
4. **异常处理**：HTTP 错误（4xx/5xx）不抛异常，而是返回状态码和错误 JSON

### `test()` — 主测试函数（12 个测试用例）

```python
def test():
```

#### 测试 1：创建 5 个用户

```
POST /users/ ×5
创建 Alice, Bob, Carol, Dave, Eve（各有不同的兴趣标签）
断言：status == 201
```

创建的用户和标签：

| 用户 | 标签 |
|------|------|
| Alice | Python, ML, basketball, photo |
| Bob | Python, Java, basketball, gaming |
| Carol | ML, photo, travel, gaming |
| Dave | Python, travel, movie, food |
| Eve | Java, movie, basketball, food |

社交图谱设计：

```
Alice ── Bob
  │  ╲   ╱
  │   ╳
  │  ╱   ╲
Dave     Carol ── Eve
```

#### 测试 2：用户列表和搜索

```
GET /users/?page=1&page_size=10    → 断言 total == 5
GET /users/?keyword=bob            → 断言 total == 1（按用户名搜索）
GET /users/?keyword=Car            → 断言 total == 1（按昵称搜索）
```

#### 测试 3：获取用户详情

```
GET /users/{alice_id}              → 断言 nickname == 'Alice'
```

#### 测试 4：更新用户信息

```
PUT /users/{alice_id}              → 仅更新 bio 字段
{"bio": "I love tech and sports"}  → 断言 bio 已更新
```

#### 测试 5：添加好友关系

```
POST /friendships/ ×5
创建 Alice-Bob, Alice-Carol, Alice-Dave, Bob-Carol, Carol-Eve
断言：status == 201, user_id < friend_id
```

#### 测试 6：获取好友列表

```
GET /users/{alice_id}/friends      → 断言 total == 3
                                   → 好友: Bob, Carol, Dave
```

#### 测试 7：检查好友关系存在性

```
GET /friendships/exists?user_id=alice&other_id=bob  → are_friends == True
GET /friendships/exists?user_id=alice&other_id=eve   → are_friends == False
```

#### 测试 8：共同好友（INTERSECT）

```
GET /users/alice/common-friends/bob
Alice 好友: Bob, Carol, Dave
Bob 好友: Alice, Carol
→ 共同好友: Carol（只有1个）
断言: count == 1, common_names == ["Carol"]
```

#### 测试 9：好友推荐（CTE + JSON_OVERLAPS）

```
GET /users/alice/recommendations?max_degree=3
→ Eve 应该被推荐（二度好友 via Carol，共同标签: movie）
断言: "Eve" in recommended_names
```

#### 测试 10：解除好友关系

```
DELETE /friendships/{friendship_id}（删除 Alice-Bob 关系）
GET /users/alice/friends           → 断言 total == 2
```

#### 测试 11：删除用户（级联删除）

```
DELETE /users/{eve_id}            → 断言 200
GET /users/{eve_id}               → 断言 404（用户已删除）
```

#### 测试 12：错误处理

| 测试 | 预期状态码 |
|------|-----------|
| 重复用户名 `alice` | `409` |
| 添加自己为好友 | `400` 或 `422` |
| 查询不存在的用户（ID=99999） | `404` |
| 无效用户名（"ab"，长度不足） | `422` |

---

## 运行入口

```python
if __name__ == "__main__":
    test()
```

**运行方式**：

```bash
# 1. 先启动后端服务
cd backend
uvicorn app.main:app --reload

# 2. 另一个终端运行测试
cd backend
python test_api.py
```

---

## 函数汇总

| 函数 | 说明 |
|------|------|
| `request(method, path, body)` | 发送 HTTP 请求并返回 `(status_code, json_body)`，自动处理 URL 编码和 JSON 序列化 |
| `test()` | 运行全部 12 个测试用例，任一断言失败则抛出 `AssertionError` |
