# 社交网络好友推荐系统

一个适合新手练手的全栈项目——用 **Vue 3 + FastAPI + MySQL** 从零搭建的社交网络，包含好友推荐算法和实时聊天。

> **🚧 阅读提示：** 这份 README 是一份**新手向导**。如果你想把代码变成自己的知识，**建议关闭 AI 辅助，对着文档手敲每一行**。理解 > 复制。

---

## 这个项目能学到什么

| 知识点 | 具体技术 |
|--------|----------|
| 数据库设计 | MySQL 表设计、无向边存储、JSON 字段实操 |
| 高级 SQL | CTE 递归查询、INTERSECT 求交集、JSON_OVERLAPS |
| ORM 实战 | SQLAlchemy 2.0 模型定义、原生 SQL 混用 |
| RESTful API | FastAPI 路由分层、Pydantic 校验、分页规范 |
| 前端架构 | Vue 3 Composition API、Vue Router 路由嵌套、Axios 封装 |
| 工程化 | Docker Compose 编排、Vite 代理、CORS 配置 |

---

## 环境准备

开始之前，你的电脑需要安装下面这些东西。如果你用的是 Windows，建议全程在 **PowerShell** 或 **Git Bash** 下操作。

| 工具 | 最低版本 | 怎么检查 |
|------|---------|---------|
| Docker Desktop | 最新版 | `docker --version` |
| Node.js | ≥ 18 | `node --version` |
| Python | ≥ 3.12 | `python --version` |

确认三个命令都能跑通再继续。

---

## 快速跑起来（先看效果）

```bash
# 第一步：起数据库和后端
docker compose up -d

# 第二步：起前端
cd frontend
npm install
npm run dev
```

浏览器打开 `http://localhost:5173` 就能看到页面了。API 文档在 `http://localhost:8000/docs`。

停服务：

```bash
docker compose down          # 保留数据
docker compose down -v       # 数据也清掉
```

---

## 从零开始手写

下面是一个**推荐的学习路线**——按照这个顺序，从数据库建表到前端页面，一步步把项目写出来。

### 架构一览

```
浏览器 (Vue 3 + Vite)
    │  http://localhost:5173
    │
    │  /api/* 请求被 Vite proxy 转发 ↓
    │
FastAPI 后端 (localhost:8000)
    │  SQLAlchemy ORM / 原生 SQL
    │
MySQL 8.0 (Docker 容器, 端口 3307)
```

**开发模式的真实情况：**

| 层 | 怎么跑 | 改了代码会怎样 |
|----|--------|:---:|
| 前端 | `npm run dev`（本机） | Vite HMR，浏览器自动刷新 ✅ |
| 后端 | Docker 容器 / 本机 `uvicorn --reload` | 容器需要 rebuild；本机即时生效 |
| 数据库 | Docker 容器 | 数据持久化在 Volume 里 |

> 建议新手把后端也放在本机跑（`uvicorn --reload`），调试更方便。Docker 只开 MySQL 就行。

---

### 第一关：数据库（MySQL）

**目标：** 设计三张表——用户、好友关系、消息，理解无向边存储。

#### 1.1 用 Docker 起 MySQL

`docker-compose.yml` 中的 `db` 服务做的几件事：
- 映射端口 `3307:3306`（避免和本地 MySQL 冲突）
- 挂载 `mysql/init/` 目录，首次启动自动建表
- 挂载 Volume 持久化数据

#### 1.2 用户表 `users`

```sql
CREATE TABLE users (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    username   VARCHAR(50)  NOT NULL UNIQUE,
    nickname   VARCHAR(100),
    tags       JSON DEFAULT (JSON_ARRAY()),   -- MySQL 8.0 原生 JSON
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**为什么用 JSON 存 tags？** 因为后面要用 `JSON_OVERLAPS` 做兴趣匹配。如果用关系表存标签，就需要多一张关联表 + JOIN；用 JSON 字段只用一行就搞定。

#### 1.3 好友关系表 `friendships`（重点）

```sql
CREATE TABLE friendships (
    id        INT AUTO_INCREMENT PRIMARY KEY,
    user_id   INT NOT NULL,
    friend_id INT NOT NULL,
    CHECK (user_id < friend_id),            -- 核心约束
    UNIQUE (user_id, friend_id)
);
```

**为什么 `CHECK(user_id < friend_id)`？** 好友关系是无向的——Alice 是 Bob 的好友，等价于 Bob 是 Alice 的好友。如果不用这个约束，每对好友会存两条记录（A→B 和 B→A），浪费存储还容易数据不一致。

**代价是什么？** 查询"用户 X 的所有好友"时不能只查一列，要查两列：

```sql
-- 用户 X 的好友 = 所有"反面"的用户
SELECT friend_id FROM friendships WHERE user_id = X
UNION
SELECT user_id FROM friendships WHERE friend_id = X
```

面试常考这个，值得亲手写一遍。

#### 1.4 消息表 `messages`

```sql
CREATE TABLE messages (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    sender_id   INT NOT NULL,       -- 谁发的
    receiver_id INT NOT NULL,       -- 发给谁
    content     TEXT NOT NULL,
    is_read     BOOLEAN DEFAULT 0,  -- MySQL 里 BOOLEAN 底层是 tinyint(1)
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

### 第二关：后端（FastAPI）

**目标：** 理解分层架构——路由层 → 服务层 → 模型层。

#### 2.1 项目分层

```
backend/app/
├── main.py          # 入口：创建 FastAPI app、注册路由、配 CORS
├── config.py        # 环境变量读取（数据库 URL 等）
├── database.py      # SQLAlchemy 引擎 + Session 工厂 + 依赖注入
├── models/          # ORM 模型（一张表一个文件）
├── schemas/         # Pydantic 请求体 / 响应体定义
├── routers/         # 路由层——只处理 HTTP 请求/响应
├── services/        # 业务逻辑层——SQL 查询在这里
└── utils/           # 分页等工具函数
```

**为什么要分这么多层？** 一个新手项目中说实话用不到全部，但这是行业标准写法。`routers/` 负责"这是 POST 还是 GET"，`services/` 负责"数据怎么查怎么算"，`schemas/` 负责"请求长什么样"。养成习惯，后面接手真项目不会懵。

#### 2.2 数据库连接（依赖注入）

FastAPI 的 `Depends(get_db)` 是怎么回事：

```python
# database.py
def get_db():
    db = SessionLocal()
    try:
        yield db          # 请求进来时创建一个 Session
    finally:
        db.close()        # 请求结束时自动关闭
```

每个 HTTP 请求拿到一个独立的数据库会话，请求结束自动释放。这就是"请求级会话"模式。

#### 2.3 好友推荐引擎（核心）

推荐函数在 `services/recommendation_service.py`，分三步走：

**第一步——CTE 递归查二度/三度好友：**

```sql
WITH RECURSIVE friend_graph AS (
    -- 基础：从目标用户出发，找一度好友
    SELECT ... FROM friendships WHERE user_id = X OR friend_id = X
    UNION ALL
    -- 递归：从当前节点再往外跳一跳
    SELECT ... FROM friendships f
    JOIN friend_graph fg ON (f.user_id = fg.connected_id OR ...)
    WHERE fg.degree < 3
)
SELECT ... WHERE degree BETWEEN 2 AND 3
```

**第二步——JSON_OVERLAPS 标签匹配：**

```sql
SELECT * FROM users
WHERE JSON_OVERLAPS(tags, '["Python","摄影"]') = 1  -- JSON 数组有交集
```

**第三步——加权打分：**

```
score = 共同好友数 × 3 + 共同标签数 × 2 + (最大度数 - 度数 + 1) × 1
```

排在前面的都是"你的好朋友也认识 + 跟你有同样兴趣"的人。

> **手写建议：** 先把 SQL 在 MySQL 客户端里跑通，再用 `text()` 嵌入 Python。直接写 ORM 版本容易绕晕。

#### 2.4 跨域 CORS

前端跑在 `localhost:5173`，后端跑在 `localhost:8000`。浏览器会因为不同端口拦截请求——这就是 **同源策略**。

两种解法：
1. **Vite proxy**（开发用）：前端 Dev Server 把 `/api` 请求转发到后端
2. **CORS 中间件**（兜底）：后端明确告诉浏览器"我允许 5173 来的请求"

这个项目两个都配了，你可以在 `main.py` 和 `vite.config.js` 里找到。

---

### 第三关：前端（Vue 3）

**目标：** 理解 SPA 路由、组件通信、API 封装。

#### 3.1 入口到路由

```
main.js → App.vue（SidebarNav + <router-view>）→ 按 URL 加载对应 View
```

路由表：
| 路径 | 页面 | 说明 |
|------|------|------|
| `/friends` | FriendsView | 好友列表 |
| `/search` | SearchView | 搜索用户 |
| `/recommend` | RecommendView | 推荐页 |
| `/messages/:userId?` | MessagesView + ChatView | 会话列表 + 聊天窗（命名视图） |
| `/profile/:id?` | ProfileView | 资料页 |

`/messages/:userId?` 用到了 Vue Router 的**命名视图**——同一个路由同时渲染两个组件（列表 + 详情），类似 Gmail 的左右分栏布局。

#### 3.2 API 封装

`src/api/index.js` 干了两件事：
1. `axios.create({ baseURL: '/api/v1' })` — 所有请求前缀统一
2. `response.interceptors` — 自动解包 `response.data`，出错时提取 `detail` 字段

注意 API 的 `baseURL` 是 `/api/v1` 而不是 `http://localhost:8000/api/v1`。因为开发时的请求链路是：

```
浏览器 → localhost:5173/api/v1/users → Vite Proxy → localhost:8000/api/v1/users
```

如果写了完整 URL，就直接绕过 proxy 了（也不会报错，但 CORS 就要单独配置）。

#### 3.3 组件通信

这个项目里常见的两种数据流：
- **路由传参：** `router.push({ name: 'Profile', params: { id: user.id } })`，目标页面用 `route.params.id` 接收
- **API 请求：** 每个页面 `onMounted` 时调 API 拿数据，赋值给 `ref()`，模板自动响应

没有用 Pinia/Vuex——因为这个规模的项目，组件内的 `ref` 就够了。等页面超过 15 个再考虑上状态管理。

---

### 第四关：Docker 编排

**目标：** 理解容器化——让数据库和后端一键启动。

`docker-compose.yml` 里值得注意的点：

**`depends_on` + `healthcheck`：**
```yaml
backend:
  depends_on:
    db:
      condition: service_healthy   # 等 MySQL 健康检查通过才启动
```
没有这个的话，backend 可能在 MySQL 还没完全就绪时就尝试连接，直接报错退出。

**Volume 挂载：**
```yaml
volumes:
  - ./mysql/init:/docker-entrypoint-initdb.d   # 首次启动自动跑 SQL
  - mysql-data:/var/lib/mysql                   # 数据持久化
```
第二个 Volume 是 named volume（不是 bind mount），Docker 管理的，删容器不会丢数据。

**Docker 里的代码不会热更新：** 如果后端跑在容器里，改了 Python 代码需要 `docker compose build backend && docker compose up -d`。开发时建议后端直接用 `uvicorn --reload` 在本机跑，Docker 只开 MySQL。

---

## 开发模式总结

```
你写前端代码    →  Vite 自动热更新        ✅ 秒级生效
你写后端代码    →  uvicorn --reload       ✅ 秒级生效（本机跑时）
                  docker compose rebuild   ❌ 需要重建镜像（容器跑时）
你改数据库      →  手动执行 SQL 或 ORM 建表  ⚠️ 注意已有数据
```

**建议的开发姿势：**
1. Docker 只开 MySQL：`docker compose up -d db`
2. 后端在本机跑：`cd backend && uvicorn app.main:app --reload --port 8000`
3. 前端在本机跑：`cd frontend && npm run dev`
4. 只改前端代码时，后端甚至不用重启

---

## API 速查

### 用户
```
POST   /api/v1/users/                      创建用户
GET    /api/v1/users/?page=1&keyword=      用户列表
GET    /api/v1/users/{id}                  用户详情
PUT    /api/v1/users/{id}                  更新用户
DELETE /api/v1/users/{id}                  删除用户
GET    /api/v1/users/{id}/friends          好友列表
GET    /api/v1/users/{id}/common-friends/{other}  共同好友
GET    /api/v1/users/{id}/recommendations        好友推荐
```

### 好友关系
```
POST   /api/v1/friendships/                添加好友
DELETE /api/v1/friendships/{id}            按 ID 解除
DELETE /api/v1/friendships/users          按用户 ID 解除
GET    /api/v1/friendships/exists          检查好友关系
```

### 消息
```
POST /api/v1/messages/                     发送消息
GET  /api/v1/messages/conversations        会话列表
GET  /api/v1/messages/?user_id=X&other_id=Y  聊天记录
PUT  /api/v1/messages/read                 标记已读
```

### 系统
```
GET  /api/v1/health                        健康检查
```

---

## 项目结构

```
tutor-db/
├── docker-compose.yml
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py
│       ├── config.py
│       ├── database.py
│       ├── models/          # user.py, friendship.py, message.py
│       ├── schemas/         # user.py, friendship.py, message.py, common.py
│       ├── routers/         # users.py, friendships.py, chat.py
│       ├── services/        # user_service, friendship_service, recommendation_service, chat_service
│       └── utils/           # pagination.py
├── frontend/
│   └── src/
│       ├── main.js
│       ├── App.vue
│       ├── api/index.js     # Axios 封装 + 所有 API 函数
│       ├── router/index.js  # 路由表
│       ├── components/      # SidebarNav.vue
│       └── views/           # 6 个页面组件
└── mysql/
    ├── init/01-init.sql
    └── conf.d/charset.cnf
```

---

## 常见问题

**Q: 前端页面打开了但没数据？**
检查后端是否在跑：浏览器打开 `http://localhost:8000/docs`。如果打不开，说明后端没启动或 MySQL 没就绪。

**Q: Docker 端口冲突？**
`docker-compose.yml` 里 MySQL 映射的是 `3307:3306`。如果你本机已经有 MySQL 占用了 3307，改成一个没用的端口。

**Q: 改了后端代码不生效？**
如果你用 `docker compose up -d` 起的后端，需要 rebuild：
```bash
docker compose build backend && docker compose up -d backend
```
建议开发时用 `uvicorn --reload` 在本机跑后端。

**Q: npm install 报错？**
确认 Node.js 版本 ≥ 18，然后删掉 `node_modules` 和 `package-lock.json` 重新安装。

**Q: 怎么重置数据库？**
```bash
docker compose down -v    # 删容器 + 删 Volume（数据全清）
docker compose up -d      # 重新启动，自动跑 init.sql
```
