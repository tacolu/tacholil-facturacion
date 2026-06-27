from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://facturacion:facturacion@localhost:5432/facturacion"
    jwt_public_key: str = ""
    jwt_algorithm: str = "RS256"
    debug: bool = False

    model_config = {"env_prefix": "FACT_", "env_file": ".env"}


settings = Settings()
