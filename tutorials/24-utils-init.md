# Utils 包初始化

> **源码文件**：`backend/app/utils/__init__.py`

---

## 文件职责

将 `utils` 子包中的 `get_pagination_slice` 函数导出，方便其他模块通过 `from app.utils import get_pagination_slice` 导入。

---

## 代码

```python
from app.utils.pagination import get_pagination_slice

__all__ = ["get_pagination_slice"]
```

---

## 使用方式

服务层模块通过以下方式导入：

```python
from app.utils.pagination import get_pagination_slice
```

> **注意**：项目中的服务层直接使用全路径 `from app.utils.pagination import get_pagination_slice` 导入，而非通过 `__init__.py` 的简短路径。两种方式都是正确的，全路径更明确。

---

## 函数汇总

| 变量 | 说明 |
|------|------|
| `__all__` | 控制通配符导入时导出的符号（仅 `get_pagination_slice` 一个函数） |
