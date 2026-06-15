# 工具函数：分页计算

> **源码文件**：`backend/app/utils/pagination.py`

---

## 文件职责

提供数据库查询使用的通用 offset/limit 计算函数，被所有服务层模块复用。

---

## 函数详解

### `get_pagination_slice(page, page_size)` — 计算分页切片参数

```python
def get_pagination_slice(page: int, page_size: int) -> tuple[int, int]:
    offset = (page - 1) * page_size
    return offset, page_size
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `page` | `int` | 页码，从 1 开始 |
| `page_size` | `int` | 每页的记录数量 |
| **返回** | `tuple[int, int]` | `(offset, limit)` 二元组 |

**计算公式**：

```
offset = (page - 1) × page_size
limit  = page_size
```

**计算示例**：

| page | page_size | offset | limit | SQL 等价 |
|------|-----------|--------|-------|----------|
| 1 | 20 | 0 | 20 | `LIMIT 20 OFFSET 0` |
| 2 | 20 | 20 | 20 | `LIMIT 20 OFFSET 20` |
| 3 | 20 | 40 | 20 | `LIMIT 20 OFFSET 40` |
| 1 | 50 | 0 | 50 | `LIMIT 50 OFFSET 0` |

**设计意图**：提取为独立函数是为了：

1. **复用**：所有服务层（user_service、friendship_service、chat_service、recommendation_service）的分页查询都使用同一个计算逻辑
2. **一致**：保证所有分页接口使用相同的 offset/limit 计算方式
3. **可维护**：如果将来需要调整分页策略（如改为游标分页），只需修改一处

---

## 函数汇总

| 函数 | 参数 | 返回 | 说明 |
|------|------|------|------|
| `get_pagination_slice()` | `page: int, page_size: int` | `(offset, limit)` | 将人类可读的页码转为数据库可用的 offset 和 limit |
