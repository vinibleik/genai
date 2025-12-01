from pydantic import PostgresDsn, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    SECRET_NUMBER: int

    SQLALCHEMY_HOST: str
    SQLALCHEMY_PORT: int
    SQLALCHEMY_DATABASE: str
    SQLALCHEMY_DRIVERNAME: str
    SQLALCHEMY_USERNAME: str
    SQLALCHEMY_PASSWORD: str
    SQLALCHEMY_ECHO: bool = False

    @computed_field
    @property
    def SQLALCHEMY_URL(self) -> PostgresDsn:  # noqa
        return PostgresDsn.build(
            scheme=self.SQLALCHEMY_DRIVERNAME,
            username=self.SQLALCHEMY_USERNAME,
            password=self.SQLALCHEMY_PASSWORD,
            host=self.SQLALCHEMY_HOST,
            port=self.SQLALCHEMY_PORT,
            path=self.SQLALCHEMY_DATABASE,
        )


settings = Settings()  # type: ignore
