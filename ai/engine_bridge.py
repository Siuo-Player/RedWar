"""Explicit boundary between Python orchestration and the Ares engine.

The bridge owns process/transport lifecycle and exposes failures explicitly.
It deliberately does not interpret RedWar rules or choose legal actions.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import os
import queue
import subprocess
import threading
import time
from abc import ABC, abstractmethod


class BridgeLifecycle(str, Enum):
    NEW = "new"
    RUNNING = "running"
    FAILED = "failed"
    CLOSED = "closed"


class EngineBridgeError(RuntimeError):
    """Base error for transport/lifecycle failures."""


class EngineBridgeTimeout(EngineBridgeError):
    """The engine did not produce a response within the bounded wait."""


class EngineBridgeProcessExit(EngineBridgeError):
    """The engine process exited before producing the expected response."""


class EngineBridgeProtocolError(EngineBridgeError):
    """The transport received a malformed or otherwise unusable response."""


@dataclass(frozen=True)
class BridgeRequest:
    request_id: int
    command: str
    sent_at: float
    state_identity: str | None


class EngineBridge(ABC):
    """Lifecycle and transport contract for an Ares engine implementation."""

    @abstractmethod
    def ensure_running(self) -> None:
        """Start the engine implementation when necessary."""

    @abstractmethod
    def send_command(self, command: str) -> None:
        """Send one complete engine command."""

    @abstractmethod
    def read_response(self, timeout: float | None = None) -> str | None:
        """Read one response line, bounded by ``timeout`` when supplied."""

    @abstractmethod
    def close(self) -> None:
        """Stop the implementation and release resources."""


class SubprocessEngineBridge(EngineBridge):
    """Subprocess-backed Ares adapter with explicit failure semantics."""

    DEFAULT_TIMEOUT = 15.0
    MAX_STDERR_LINES = 40

    def __init__(self, executable_path: str):
        if not executable_path:
            raise ValueError("executable_path must not be empty")
        self.exe_path = os.path.abspath(executable_path)
        self.project_root = os.path.dirname(
            os.path.dirname(os.path.dirname(self.exe_path))
        )
        self.process: subprocess.Popen[str] | None = None
        self.lifecycle = BridgeLifecycle.NEW
        self._response_queue: queue.Queue[str] = queue.Queue()
        self._reader_threads: list[threading.Thread] = []
        self._stderr_lines: list[str] = []
        self._request_counter = 0
        self.last_request: BridgeRequest | None = None
        self.last_error: EngineBridgeError | None = None

    @property
    def stderr_tail(self) -> tuple[str, ...]:
        return tuple(self._stderr_lines)

    @property
    def last_request_id(self) -> int | None:
        return self.last_request.request_id if self.last_request else None

    @property
    def process(self):
        return self._process

    @process.setter
    def process(self, value):
        self._process = value

    def _start_reader(self, stream, target):
        thread = threading.Thread(target=target, args=(stream,), daemon=True)
        thread.start()
        self._reader_threads.append(thread)

    def _read_stdout(self, stream) -> None:
        try:
            for line in stream:
                self._response_queue.put(line.rstrip("\r\n"))
        finally:
            self._response_queue.put("")

    def _read_stderr(self, stream) -> None:
        try:
            for line in stream:
                text = line.rstrip("\r\n")
                self._stderr_lines.append(text)
                if len(self._stderr_lines) > self.MAX_STDERR_LINES:
                    del self._stderr_lines[0]
        except (ValueError, OSError):
            pass

    def ensure_running(self) -> None:
        if self.process is not None and self.process.poll() is None:
            self.lifecycle = BridgeLifecycle.RUNNING
            return

        if self.lifecycle == BridgeLifecycle.CLOSED:
            raise EngineBridgeError("engine bridge is closed")
        if not os.path.exists(self.exe_path):
            self.lifecycle = BridgeLifecycle.FAILED
            error = EngineBridgeProcessExit(
                f"Executável C++ não encontrado em: {self.exe_path}. Usa o script de build primeiro!"
            )
            self.last_error = error
            raise error

        self._response_queue = queue.Queue()
        self._stderr_lines = []
        self._reader_threads = []
        try:
            self.process = subprocess.Popen(
                [self.exe_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                cwd=self.project_root,
                bufsize=1,
            )
        except OSError as exc:
            self.lifecycle = BridgeLifecycle.FAILED
            error = EngineBridgeProcessExit(f"failed to start Ares: {exc}")
            self.last_error = error
            raise error from exc

        self.lifecycle = BridgeLifecycle.RUNNING
        self._start_reader(self.process.stdout, self._read_stdout)
        self._start_reader(self.process.stderr, self._read_stderr)
        self.send_command("isready")

    def _state_identity(self, command: str) -> str | None:
        prefix = "position rwen "
        if command.startswith(prefix):
            payload = command[len(prefix):].strip().encode("utf-8")
            return hashlib.sha256(payload).hexdigest()
        return self.last_request.state_identity if self.last_request else None

    def send_command(self, command: str) -> None:
        if not isinstance(command, str) or not command.strip():
            raise EngineBridgeProtocolError("command must be a non-empty string")
        if self.process is None:
            raise EngineBridgeError("Engine process is not running")
        if self.process.poll() is not None or self.process.stdin is None:
            self.lifecycle = BridgeLifecycle.FAILED
            error = EngineBridgeProcessExit("Engine process is not running")
            self.last_error = error
            raise error
        try:
            self.process.stdin.write(command + "\n")
            self.process.stdin.flush()
        except (BrokenPipeError, OSError) as exc:
            self.lifecycle = BridgeLifecycle.FAILED
            error = EngineBridgeProcessExit(f"engine write failed: {exc}")
            self.last_error = error
            raise error from exc

        self._request_counter += 1
        self.last_request = BridgeRequest(
            request_id=self._request_counter,
            command=command,
            sent_at=time.monotonic(),
            state_identity=self._state_identity(command),
        )

    def read_response(self, timeout: float | None = None) -> str | None:
        if timeout is None:
            timeout = self.DEFAULT_TIMEOUT
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        self.ensure_running()

        try:
            response = self._response_queue.get(timeout=timeout)
        except queue.Empty as exc:
            error = EngineBridgeTimeout(
                f"timeout waiting for Ares response (request_id={self.last_request_id})"
            )
            self.last_error = error
            raise error from exc

        if response == "":
            returncode = self.process.poll() if self.process is not None else None
            self.lifecycle = BridgeLifecycle.FAILED
            error = EngineBridgeProcessExit(
                f"Ares exited before response (request_id={self.last_request_id}, returncode={returncode})"
            )
            self.last_error = error
            raise error
        return response.strip()

    def close(self) -> None:
        process = self.process
        self.process = None
        self.lifecycle = BridgeLifecycle.CLOSED
        if process is None:
            return

        try:
            if process.poll() is None and process.stdin is not None:
                process.stdin.write("quit\n")
                process.stdin.flush()
        except (BrokenPipeError, OSError):
            pass

        try:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=1)
        except (subprocess.TimeoutExpired, OSError):
            try:
                process.kill()
                process.wait(timeout=1)
            except OSError:
                pass

    def restart(self) -> None:
        """Bounded recovery primitive: close the failed process and start a new one."""
        if self.lifecycle == BridgeLifecycle.CLOSED:
            raise EngineBridgeError("cannot restart a closed bridge")
        self.close()
        self.lifecycle = BridgeLifecycle.FAILED
        self.last_error = None
        self.process = None
        self.ensure_running()

    def __enter__(self) -> "SubprocessEngineBridge":
        self.ensure_running()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()
