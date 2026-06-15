# ============================================================
# 社交网络后端 FastAPI 服务镜像
# ============================================================
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖（cryptography 需要 libffi 等编译环境）
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        libffi-dev \
        default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# 先复制依赖文件，利用 Docker 缓存层
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY app/ ./app/

# 暴露 FastAPI 默认端口
EXPOSE 8000

# 启动 uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
