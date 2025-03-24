from __future__ import annotations

import uuid
from functools import cache
from os import PathLike
from pathlib import Path
from typing import Annotated

import numpy as np
import portalocker
from fastembed import TextEmbedding
from pydantic import BaseModel, Field

from mcp_toolbox.config import Config
from mcp_toolbox.log import logger

embedding_model = TextEmbedding()
logger.info("The model BAAI/bge-small-en-v1.5 is ready to use.")


def embed_text(text: str) -> list[float]:
    return next(iter(embedding_model.embed([text])))


class MemoryModel(BaseModel):
    session_id: Annotated[str, Field(description="The session id of the memory")]
    brief: Annotated[str, Field(description="The brief information of the memory")]
    detail: Annotated[str, Field(description="The detailed information of the brief text")]
    embedding: Annotated[list[float] | None, Field(description="The embedding of the brief text")] = None


@cache
def get_current_session_memory() -> LocalMemory:
    return LocalMemory.new_session()


class LocalMemory:
    @classmethod
    def new_session(cls) -> LocalMemory:
        return cls.use_session(uuid.uuid4().hex)

    @classmethod
    def use_session(cls, session_id: str) -> LocalMemory:
        config = Config()
        return cls(session_id, config.memory_file)

    def __init__(self, session_id: str, memory_file: PathLike):
        self.session_id = session_id
        self.memory_file = Path(memory_file)

        self.memory_file.parent.mkdir(parents=True, exist_ok=True)
        self.memory_file.touch(exist_ok=True)
        self.current_memory: np.ndarray = self._load()

    def _load(self) -> np.ndarray:
        if not self.memory_file.exists():
            return np.empty((0, 4), dtype=object)

        try:
            with portalocker.Lock(self.memory_file, "rb") as f:
                memory = np.load(f, allow_pickle=True)
        except Exception as e:
            logger.warning(f"Error loading memory: {e}")
            memory = np.empty((0, 4), dtype=object)

        return memory

    def store(self, brief: str, detail: str) -> MemoryModel:
        try:
            # Keep the file locked during the entire operation
            with portalocker.Lock(self.memory_file, "rb+") as f:
                try:
                    # Load existing memory
                    current_memory = np.load(f, allow_pickle=True)
                except (ValueError, EOFError):
                    # File is empty or not a valid numpy array
                    current_memory = np.empty((0, 4), dtype=object)

                embedding = embed_text(brief)

                # Append the new entry
                if current_memory.size == 0:
                    # Initialize with first entry including all 4 fields
                    updated_memory = np.array([[self.session_id, brief, detail, embedding]], dtype=object)
                else:
                    updated_memory = np.append(
                        current_memory,
                        np.array([[self.session_id, brief, detail, embedding]], dtype=object),
                        axis=0,
                    )

                # Save the updated memory
                f.seek(0)
                f.truncate()
                np.save(f, updated_memory)
        except Exception as e:
            logger.warning(f"Error storing memory: {e}")
            raise

        self.current_memory = self._load()

        return MemoryModel(
            session_id=self.session_id,
            brief=brief,
            detail=detail,
            embedding=embedding,
        )

    def query(
        self,
        query: str,
        top_k: int = 3,
        cross_session: bool = True,
        refresh: bool = False,
    ) -> list[MemoryModel]:
        if refresh:
            self.current_memory = self._load()
        embedding = embed_text(query)

        # Check if memory is empty
        if self.current_memory.size == 0:
            return []

        # Filter by session if cross_session is False
        if not cross_session:
            # Create a mask for entries from the current session
            session_mask = self.current_memory[:, 0] == self.session_id
            if not any(session_mask):
                return []  # No entries for current session

            # Filter memory to only include current session
            filtered_memory = self.current_memory[session_mask]

            # Calculate similarity between query embedding and each stored embedding
            similarity = np.array([np.dot(stored_embedding, embedding) for stored_embedding in filtered_memory[:, 3]])
            top_k_idx = np.argsort(similarity)[-min(top_k, len(similarity)) :]

            return [
                MemoryModel(
                    session_id=filtered_memory[idx, 0],
                    brief=filtered_memory[idx, 1],
                    detail=filtered_memory[idx, 2],
                )
                for idx in top_k_idx
            ]
        else:
            # Calculate similarity between query embedding and each stored embedding
            similarity = np.array([
                np.dot(stored_embedding, embedding) for stored_embedding in self.current_memory[:, 3]
            ])
            top_k_idx = np.argsort(similarity)[-min(top_k, len(similarity)) :]

            return [
                MemoryModel(
                    session_id=self.current_memory[idx, 0],
                    brief=self.current_memory[idx, 1],
                    detail=self.current_memory[idx, 2],
                )
                for idx in top_k_idx
            ]

    def clear(self):
        # Create an empty memory array
        empty_memory = np.empty((0, 4), dtype=object)

        # Update the file with the empty array
        with portalocker.Lock(self.memory_file, "wb") as f:
            np.save(f, empty_memory)

        # Update the current memory
        self.current_memory = empty_memory
