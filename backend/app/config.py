from pydantic_settings import BaseSettings, SettingsConfigDict
class Settings(BaseSettings):
    app_env: str = "development"
    app_name: str = "AscentIntegrity"
    secret_key: str = "unsafe-development-secret-change-before-use"
    database_url: str = "postgresql+psycopg://ascent:change-me@localhost:5432/ascentintegrity"
    storage_root: str = "./private_storage"
    max_upload_bytes: int = 15 * 1024 * 1024
    allow_dev_registration: bool = True
    cors_origins: str = "http://localhost:5173"
    blockchain_rpc_url: str = ""
    blockchain_contract_address: str = ""
    blockchain_private_key: str = ""
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
settings = Settings()
