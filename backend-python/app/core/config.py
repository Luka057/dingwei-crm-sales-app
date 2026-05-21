"""
应用配置 — 从环境变量读取,经 pydantic 类型校验。

参考:`../../docs/需求文档-v2.md §11.1` O2 决议(SQL Server Mac 跑法)。
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """全局配置单例,启动时校验 .env。"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── 运行环境 ────────────────────────────────────────────────
    env: Literal["dev", "test", "staging", "prod"] = "dev"
    debug: bool = False
    app_name: str = "dingwei-crm-backend"
    api_v1_prefix: str = "/api/v1"

    # ── 数据库 ──────────────────────────────────────────────────
    # 默认 docker 内连接;Mac 本机直跑改 sqlserver → localhost
    database_url: str = Field(
        default=(
            "mssql+aioodbc://sa:Dingwei!Strong#2026@sqlserver:1433/dingwei_crm_sales"
            "?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"
        ),
        description="SQLAlchemy async URL (aioodbc + SQL Server)",
    )
    db_echo: bool = False  # True 时打印 SQL,调试用

    # ── 鉴权 ────────────────────────────────────────────────────
    jwt_secret: SecretStr = Field(
        default=SecretStr("change_me_in_prod_or_will_be_breached"),
        description="JWT HS256 签发密钥;生产必须 .env 覆盖",
    )
    jwt_algorithm: Literal["HS256"] = "HS256"
    jwt_access_token_expire_minutes: int = 60 * 24 * 7  # 7 天(试点期,Phase 1B 加 refresh)

    # ── AI(Phase 1B 才启用,1A 留位) ─────────────────────────
    deepseek_api_key: SecretStr = Field(
        default=SecretStr("change_me"),
        description="DeepSeek API key,1A 不使用",
    )

    # ── 缓存(infra 留位,1A 不写代码) ───────────────────────
    redis_url: str = "redis://redis:6379"

    # ── 照片上传(Q7 决议:完整可用) ────────────────────────
    upload_dir: str = "./uploads"
    upload_max_size_bytes: int = 5 * 1024 * 1024  # 5MB
    upload_allowed_mimes: tuple[str, ...] = (
        "image/jpeg",
        "image/png",
    )
    # O3 悬挂:per-user 限速,实施时定;先用建议初值
    upload_rate_limit_per_hour: int = 30
    upload_rate_limit_per_day: int = 100

    # ── CORS(前端 vite dev 默认 5173) ───────────────────────
    cors_origins: tuple[str, ...] = (
        "http://localhost:5173",
        "http://localhost:8080",
    )

    @property
    def database_url_sync(self) -> str:
        """同步版 URL,Alembic 用(env.py 里转 async)。"""
        return self.database_url.replace("mssql+aioodbc", "mssql+pyodbc", 1)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """单例,启动时校验一次。"""
    return Settings()
