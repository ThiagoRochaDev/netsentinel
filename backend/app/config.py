from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="", extra="ignore")

    secret_key: str
    admin_username: str = "admin"
    admin_password_hash: str

    netsentinel_env: str = "development"
    netsentinel_log_level: str = "info"
    netsentinel_db_path: str = "/data/netsentinel.db"

    netsentinel_iface: str = ""
    netsentinel_lan_cidr: str = ""

    access_token_expire_minutes: int = 60 * 12
    jwt_algorithm: str = "HS256"

    discovery_scan_interval_seconds: int = 120
    suricata_eve_path: str = "/var/log/suricata/eve.json"

    device_online_threshold_minutes: int = 10

    high_connection_rate_threshold: int = 200
    high_connection_rate_window_seconds: int = 60
    suricata_alert_severity_threshold: int = 3

    retention_days_events: int = 30
    retention_days_connections: int = 30
    retention_days_alerts: int = 365
    retention_sweep_interval_seconds: int = 6 * 60 * 60

    login_rate_limit_attempts: int = 5
    login_rate_limit_window_seconds: int = 300


@lru_cache
def get_settings() -> Settings:
    return Settings()
