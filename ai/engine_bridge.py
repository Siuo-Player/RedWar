"""Explicit boundary between Python orchestration and the Ares engine."""

from __future__ import annotations

import os
import subprocess
from abc import ABC, abstractmethod


class EngineBridge(ABC):
    """Lifecycle and transport contract for an Ares engine implementation."""

    @abstractmethod
    def ensure_running(self) -> None:
        """Start the engine implementation when necessary."""

    @abstractmethod
    def send_command(self, command: str) -> None:
        """Send one complete engine command."""

    @abstractmethod
    def read_response(self) -> str | None:
        """Read one complete response line, or ``None`` when unavailable."""

    @abstractmethod
    def close(self) -> None:
        """Stop the implementation and release resources."""


class SubprocessEngineBridge(EngineBridge):
    """Current compatibility implementation backed by the Ares CLI."""

    def __init__(self, executable_path: str):
        if not executable_path:
            raise ValueError("executable_path must not be empty")
        self.exe_path = os.path.abspath(executable_path)
        # <repo>/ai/cpp_engine/engine -> <repo>
        self.project_root = os.path.dirname(
            os.path.dirname(os.path.dirname(self.exe_path))
        )
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
        if self.process is None:
            raise RuntimeError("Engine process is not running")
        if self.process.poll() is not None or self.process.stdin is None:
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
        if process is None or process.poll() is not None:
            return

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
