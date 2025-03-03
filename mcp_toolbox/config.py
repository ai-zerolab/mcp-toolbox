from pathlib import Path

from pydantic_settings import BaseSettings

HOME = Path("~/.zerolab/mcp-toolbox").expanduser()


class Config(BaseSettings):
    figma_api_key: str | None = None

    cache_dir: str = (HOME / "cache").expanduser().resolve().absolute().as_posix()


if __name__ == "__main__":
    print(Config())
