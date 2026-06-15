"""
分页工具函数
用于数据库查询的通用 offset/limit 计算
"""


def get_pagination_slice(page: int, page_size: int) -> tuple[int, int]:
    """
    根据页码和每页数量计算 offset 和 limit

    Args:
        page: 页码（从1开始）
        page_size: 每页数量

    Returns:
        (offset, limit) 二元组
    """
    offset = (page - 1) * page_size
    return offset, page_size
