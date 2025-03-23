# TODO: Implement local memory bank for users to store information

from __future__ import annotations

import uuid
from os import PathLike
from pathlib import Path

from pydantic import BaseModel

from mcp_toolbox.config import Config


class MemoryModel(BaseModel):
    pass


class LocalMemory:
    @classmethod
    def new_session(cls) -> LocalMemory:
        config = Config()

        session_id = uuid.uuid4().hex
        return cls(session_id, config.memory_dir)

    def __init__(self, session_id: str, memory_file: PathLike):
        self.session_id = session_id
        self.memory_file = Path(memory_file)

        self.memory_file.parent.mkdir(parents=True, exist_ok=True)
