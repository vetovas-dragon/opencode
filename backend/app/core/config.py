from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "在线问诊教学系统"
    app_env: str = "dev"
    debug: bool = True
    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 720

    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_user: str = "otc"
    mysql_password: str = "otc_pass_2026"
    mysql_db: str = "otc"

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0

    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "otc_minio"
    minio_secret_key: str = "otc_minio_2026"
    minio_bucket: str = "otc-files"
    minio_secure: bool = False

    xfyun_app_id: str = ""
    xfyun_api_key: str = ""
    xfyun_api_secret: str = ""

    sms_provider: str = "mock"
    push_provider: str = "mock"

    cors_origins: str = "http://localhost:5173,http://localhost:8080"

    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_db}?charset=utf8mb4"
        )

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
