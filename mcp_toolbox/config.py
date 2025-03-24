import platform
from pathlib import Path

from pydantic_settings import BaseSettings


class Config(BaseSettings):
    figma_api_key: str | None = None
    tavily_api_key: str | None = None
    duckduckgo_api_key: str | None = None
    bfl_api_key: str | None = None

    enable_commond_tools: bool = True
    enable_file_ops_tools: bool = True
    enable_audio_tools: bool = True
    enabel_enhance_tools: bool = True
    tool_home: str = Path("~/.zerolab/mcp-toolbox").expanduser().as_posix()

    @property
    def cache_dir(self) -> str:
        return (Path(self.tool_home) / "cache").expanduser().resolve().absolute().as_posix()

    @property
    def memory_file(self) -> str:
        # Use Documents folder for macOS to enable sync across multiple Mac devices
        if platform.system() == "Darwin":  # macOS
            documents_path = Path("~/Documents/zerolab/mcp-toolbox").expanduser()
            documents_path.mkdir(parents=True, exist_ok=True)
            return (documents_path / "memory").resolve().absolute().as_posix()
        else:
            # Default behavior for other operating systems
            return (Path(self.tool_home) / "memory").expanduser().resolve().absolute().as_posix()


if __name__ == "__main__":
    print(Config())
