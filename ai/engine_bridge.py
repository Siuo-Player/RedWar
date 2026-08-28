"""Engine bridge boundary used by Python AI orchestration.

The default implementation remains a subprocess adapter for the current Ares
CLI.  Keeping the boundary explicit lets a future in-process C++ binding
implement the same contract without changing callers such as ``CppEngineBot``.
"""

from __future__ import annotations

import os
import subprocess
import sys
from abc import ABC, abstractmethod
from typing import IO


class EngineBridge(ABC):
    """Minimal lifecycle/protocol contract between Python and an engine."""

    @abstractmethod
    def ensure_running(self) -> None:
        """Start or reconnect to the engine implementation."""

    @abstractmethod
    def send_command(self, command: str) -> None:
        """Send one protocol command to the engine."""

    @abstractmethod
    def read_response(self) -> str | None:
        """Read one complete engine response line, or ``None`` when unavailable."""

    @abstractmethod
    def close(self) -> None:
        """Stop the implementation and release its resources."""


class SubprocessEngineBridge(EngineBridge):
    """Current transitional Ares bridge backed by the command-line engine."""

    def __init__(self, executable_path: str):
        if not executable_path:
            raise ValueError("executable_path must not be empty")
        self.exe_path = os.path.abspath(executable_path)
        self.project_root = os.path.dirname(os.path.dirname(self.exe_path))
        self.process: subprocess.Popen[str] | None = None

    def ensure_running(self) -> None:
        if self.process is not None and self.process.poll() is None:
            return

        if not os.path.exists(self.exe_path):
            raise FileNotFoundError(
                f"Executável C++ não encontrado em: {self.exe_path}. "
                "Usa o script de build primeiro!"
            )

        self.process = subprocess.Popen(
            [self.exe_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            cwd=self.project_root,
        )
        self.send_command("isready")

    def send_command(self, command: str) -> None:
        self.ensure_running() if self.process is None else None
        if self.process is None or self.process.poll() is not None or self.process.stdin is None:
            raise RuntimeError("Engine process is not running")
        self.process.stdin.write(command + "\n")
        self.process.stdin.flush()

    def read_response(self) -> str | None:
        self.ensure_running()
        if self.process is None or self.process.poll() is not None or self.process.stdout is None:
            return None
        return self.process.stdout.readline().strip()

    def close(self) -> None:
        process = self.process
        self.process = None
        if process is None:
            return

        if process.poll() is None:
            try:
                if process.stdin is not None:
                    process.stdin.write("quit\n")
                    process.stdin.flush()
            except (BrokenPipeError, OSError):
                pass
            try:
                process.terminate()
                process.wait(timeout=1)
            except (subprocess.TimeoutExpired, OSError):
                try:
                    process.kill()
                    process.wait(timeout=1)
                except OSError:
                    pass

    def __enter__(self) -> "SubprocessEngineBridge":
        self.ensure_running()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()
