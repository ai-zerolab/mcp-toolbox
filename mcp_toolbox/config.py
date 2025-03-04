from pathlib import Path

from pydantic_settings import BaseSettings


class Config(BaseSettings):
    figma_api_key: str | None = None

    enable_commond_tools: bool = True
    enable_file_ops_tools: bool = True
    tool_home: str = Path("~/.zerolab/mcp-toolbox").expanduser()

    @property
    def cache_dir(self) -> str:
        return (self.tool_home / "cache").expanduser().resolve().absolute().as_posix()


if __name__ == "__main__":
    print(Config())
