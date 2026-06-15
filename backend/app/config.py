"""
应用配置模块
通过 pydantic-settings 从 .env 文件和环境变量加载数据库连接参数
"""
from urllib.parse import quote_plus
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """数据库和应用配置"""

    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    DB_NAME: str = "social_network"
    DB_ECHO: bool = False

    @property
    def DATABASE_URL(self) -> str:
        """构建 MySQL 连接 URL，使用 pymysql 驱动 + utf8mb4 编码"""
        # URL 编码用户名和密码，防止 @ / : 等特殊字符破坏 URL 格式
        encoded_user = quote_plus(self.DB_USER)
        encoded_password = quote_plus(self.DB_PASSWORD)
        return (
            f"mysql+pymysql://{encoded_user}:{encoded_password}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            f"?charset=utf8mb4"
        )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,#大小写敏感
    }


settings = Settings()
