from pydantic_settings import BaseSettings


class Config(BaseSettings):
    figma_api_key: str | None = None


if __name__ == "__main__":
    print(Config())
