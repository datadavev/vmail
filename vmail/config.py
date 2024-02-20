import functools
import os
import typing
import pydantic_settings

current_folder = os.path.dirname(os.path.realpath(__file__))
class Settings(pydantic_settings.BaseSettings):
    model_config = pydantic_settings.SettingsConfigDict(
        env_prefix="VMAIL_", env_file=".env"
    )
    smtp_host: str = "sandbox.smtp.mailtrap.io"
    smtp_port: int = 2525
    smtp_user: str = "user"
    smtp_password: str = "password"
    smtp_from: str = "noreply@example.com"
    smtp_name: str = "Mail Verification"
    smtp_starttls: bool = False
    smtp_ssl: bool = True
    smtp_credentials: bool = True
    smtp_checkcerts: bool = True
    verify_seed: str = "replace me with some random seed string"
    verify_url: str = "http://localhost:8001/verify/{token}"
    verify_timeout_seconds: float = 15 * 60
    otp_digits: int = 6
    db_connection_string: str = "sqlite:///test.db"
    api_keys: typing.Dict[str, str] = {"test": "test"}
    template_path: str = os.path.join(current_folder, "templates")


@functools.lru_cache()
def get_settings(env_file: typing.Optional[str] = None) -> Settings:
    if env_file is None:
        env_file = ".env"
    return Settings(_env_file=env_file)
