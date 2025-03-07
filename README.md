# mcp-toolbox

[![Release](https://img.shields.io/github/v/release/ai-zerolab/mcp-toolbox)](https://img.shields.io/github/v/release/ai-zerolab/mcp-toolbox)
[![Build status](https://img.shields.io/github/actions/workflow/status/ai-zerolab/mcp-toolbox/main.yml?branch=main)](https://github.com/ai-zerolab/mcp-toolbox/actions/workflows/main.yml?query=branch%3Amain)
[![codecov](https://codecov.io/gh/ai-zerolab/mcp-toolbox/branch/main/graph/badge.svg)](https://codecov.io/gh/ai-zerolab/mcp-toolbox)
[![Commit activity](https://img.shields.io/github/commit-activity/m/ai-zerolab/mcp-toolbox)](https://img.shields.io/github/commit-activity/m/ai-zerolab/mcp-toolbox)
[![License](https://img.shields.io/github/license/ai-zerolab/mcp-toolbox)](https://img.shields.io/github/license/ai-zerolab/mcp-toolbox)

A comprehensive toolkit for enhancing LLM capabilities through the Model Context Protocol (MCP). This package provides a collection of tools that allow LLMs to interact with external services and APIs, extending their functionality beyond text generation.

- **GitHub repository**: <https://github.com/ai-zerolab/mcp-toolbox/>
- (WIP)**Documentation**: <https://ai-zerolab.github.io/mcp-toolbox/>

## Features

> \*nix is our main target, but Windows should work too.

- **Command Line Execution**: Execute any command line instruction through LLM
- **Figma Integration**: Access Figma files, components, styles, and more
- **Extensible Architecture**: Easily add new API integrations
- **MCP Protocol Support**: Compatible with Claude Desktop and other MCP-enabled LLMs
- **Comprehensive Testing**: Well-tested codebase with high test coverage

## Installation

### Using uv (Recommended)

We recommend using [uv](https://github.com/astral-sh/uv) to manage your environment.

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh  # For macOS/Linux
# or
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"  # For Windows
```

Then you can use `uvx mcp-toolbox@latest stdio` as commands for running the MCP server for latest version.

### Installing via Smithery

To install Toolbox for LLM Enhancement for Claude Desktop automatically via [Smithery](https://smithery.ai/server/@ai-zerolab/mcp-toolbox):

```bash
npx -y @smithery/cli install @ai-zerolab/mcp-toolbox --client claude
```

### Using pip

```bash
pip install mcp-toolbox
```

And you can use `mcp-toolbox stdio` as commands for running the MCP server.

## Configuration

### Environment Variables

The following environment variables can be configured:

- `FIGMA_API_KEY`: API key for Figma integration

### Claude Desktop Configuration

To use mcp-toolbox with Claude Desktop, add the following to your Claude Desktop configuration file:

```json
{
  "mcpServers": {
    "zerolab-toolbox": {
      "command": "uvx",
      "args": ["mcp-toolbox@latest", "stdio"],
      "env": {
        "FIGMA_API_KEY": "your-figma-api-key"
      }
    }
  }
}
```

You can generate a debug configuration template using:

```bash
uv run generate_config_template.py
```

## Available Tools

### Command Line Tools

| Tool              | Description                        |
| ----------------- | ---------------------------------- |
| `execute_command` | Execute a command line instruction |

### File Operations Tools

| Tool                 | Description                                         |
| -------------------- | --------------------------------------------------- |
| `read_file_content`  | Read content from a file                            |
| `write_file_content` | Write content to a file                             |
| `replace_in_file`    | Replace content in a file using regular expressions |
| `list_directory`     | List directory contents with detailed information   |

### Figma Tools

| Tool                            | Description                              |
| ------------------------------- | ---------------------------------------- |
| `figma_get_file`                | Get a Figma file by key                  |
| `figma_get_file_nodes`          | Get specific nodes from a Figma file     |
| `figma_get_image`               | Get images for nodes in a Figma file     |
| `figma_get_image_fills`         | Get URLs for images used in a Figma file |
| `figma_get_comments`            | Get comments on a Figma file             |
| `figma_post_comment`            | Post a comment on a Figma file           |
| `figma_delete_comment`          | Delete a comment from a Figma file       |
| `figma_get_team_projects`       | Get projects for a team                  |
| `figma_get_project_files`       | Get files for a project                  |
| `figma_get_team_components`     | Get components for a team                |
| `figma_get_file_components`     | Get components from a file               |
| `figma_get_component`           | Get a component by key                   |
| `figma_get_team_component_sets` | Get component sets for a team            |
| `figma_get_team_styles`         | Get styles for a team                    |
| `figma_get_file_styles`         | Get styles from a file                   |
| `figma_get_style`               | Get a style by key                       |

### XiaoyuZhouFM Tools

| Tool                    | Description                                                                                |
| ----------------------- | ------------------------------------------------------------------------------------------ |
| `xiaoyuzhoufm_download` | Download a podcast episode from XiaoyuZhouFM with optional automatic m4a to mp3 conversion |

### Audio Tools

| Tool               | Description                                                      |
| ------------------ | ---------------------------------------------------------------- |
| `get_audio_length` | Get the length of an audio file in seconds                       |
| `get_audio_text`   | Get transcribed text from a specific time range in an audio file |

## Usage Examples

### Running the MCP Server

```bash
# Run with stdio transport (default)
mcp-toolbox stdio

# Run with SSE transport
mcp-toolbox sse --host localhost --port 9871
```

### Using with Claude Desktop

1. Configure Claude Desktop as shown in the Configuration section
1. Start Claude Desktop
1. Ask Claude to interact with Figma files:
   - "Can you get information about this Figma file: 12345abcde?"
   - "Show me the components in this Figma file: 12345abcde"
   - "Get the comments from this Figma file: 12345abcde"
1. Ask Claude to execute command line instructions:
   - "What files are in the current directory?"
   - "What's the current system time?"
   - "Show me the contents of a specific file."
1. Ask Claude to download podcasts from XiaoyuZhouFM:
   - "Download this podcast episode: https://www.xiaoyuzhoufm.com/episode/67c3d80fb0167b8db9e3ec0f"
   - "Download and convert to MP3 this podcast: https://www.xiaoyuzhoufm.com/episode/67c3d80fb0167b8db9e3ec0f"
1. Ask Claude to work with audio files:
   - "What's the length of this audio file: audio.m4a?"
   - "Transcribe the audio from 60 to 90 seconds in audio.m4a"
   - "Get the text from 2:30 to 3:00 in the audio file"

## Development

### Local Setup

Fork the repository and clone it to your local machine.

```bash
# Install in development mode
make install
# Activate a virtual environment
source .venv/bin/activate  # For macOS/Linux
# or
.venv\Scripts\activate  # For Windows
```

### Running Tests

```bash
make test
```

### Running Checks

```bash
make check
```

### Building Documentation

```bash
make docs
```

## Adding New Tools

To add a new API integration:

1. Update `config.py` with any required API keys
1. Create a new module in `mcp_toolbox/`
1. Implement your API client and tools
1. Add tests for your new functionality
1. Update the README.md with new environment variables and tools

See the [development guide](llms.txt) for more detailed instructions.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
1. Create a feature branch (`git checkout -b feature/amazing-feature`)
1. Commit your changes (`git commit -m 'Add some amazing feature'`)
1. Push to the branch (`git push origin feature/amazing-feature`)
1. Open a Pull Request

## License

This project is licensed under the terms of the license included in the repository.
