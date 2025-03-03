# mcp-toolbox

[![Release](https://img.shields.io/github/v/release/ai-zerolab/mcp-toolbox)](https://img.shields.io/github/v/release/ai-zerolab/mcp-toolbox)
[![Build status](https://img.shields.io/github/actions/workflow/status/ai-zerolab/mcp-toolbox/main.yml?branch=main)](https://github.com/ai-zerolab/mcp-toolbox/actions/workflows/main.yml?query=branch%3Amain)
[![codecov](https://codecov.io/gh/ai-zerolab/mcp-toolbox/branch/main/graph/badge.svg)](https://codecov.io/gh/ai-zerolab/mcp-toolbox)
[![Commit activity](https://img.shields.io/github/commit-activity/m/ai-zerolab/mcp-toolbox)](https://img.shields.io/github/commit-activity/m/ai-zerolab/mcp-toolbox)
[![License](https://img.shields.io/github/license/ai-zerolab/mcp-toolbox)](https://img.shields.io/github/license/ai-zerolab/mcp-toolbox)

Maintenance of a set of tools to enhance LLM through MCP protocols.

- **Github repository**: <https://github.com/ai-zerolab/mcp-toolbox/>
- **Documentation**(WIP) <https://ai-zerolab.github.io/mcp-toolbox/>

## Installation

We recommend using [uv](https://github.com/astral-sh/uv) to manage your environment.

You can use `curl -LsSf https://astral.sh/uv/install.sh | sh` to install uv on macOS and Linux.

> \*nix is our main target, but Windows should work too.

```json
{
  "mcpServers": {
    "zerolab-toolbox": {
      "command": "uvx",
      "args": ["mcp-toolbox", "stdio"],
      "env": {
        "FIGMA_API_KEY": ""
      }
    }
  }
}
```

## Development

Local install with uv:

```bash
make install
```

Run tests:

```bash
make test
```

Run checks:

```bash
make check
```

Build docs:

```bash
make docs
```

Use following command to generate debug config:

```bash
uv run generate_config_template.py
```
