import json
import shutil
import sys
from pathlib import Path

from mcp_toolbox.config import Config


def get_endpoint_path() -> str:
    """
    Find the path to the mcp-toolbox script.
    Similar to the 'which' command in Unix-like systems.

    Returns:
        str: The full path to the mcp-toolbox script
    """
    # First try using shutil.which to find the script in PATH
    script_path = shutil.which("mcp-toolbox")
    if script_path:
        return script_path

    # If not found in PATH, try to find it in the current Python environment
    # This handles cases where the script is installed but not in PATH
    bin_dir = Path(sys.executable).parent
    possible_paths = [
        bin_dir / "mcp-toolbox",
        bin_dir / "mcp-toolbox.exe",  # For Windows
    ]

    for path in possible_paths:
        if path.exists():
            return str(path)

    # If we can't find it, return the script name and hope it's in PATH when executed
    return "mcp-toolbox"


if __name__ == "__main__":
    endpoint_path = get_endpoint_path()

    mcp_config = {
        "command": endpoint_path,
        "args": ["stdio"],
        "env": {field.upper(): "" for field in Config.model_fields},
    }

    mcp_item = {
        "zerolab-toolbox-dev": mcp_config,
    }

    print(json.dumps(mcp_item, indent=4))
