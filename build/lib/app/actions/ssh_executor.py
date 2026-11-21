from dataclasses import dataclass
from pathlib import Path
import socket

import paramiko

from app.config import Settings


class SshNotConfiguredError(RuntimeError):
    """Raised when execution is requested but no target host is configured."""


class SshExecutionError(RuntimeError):
    """Raised when the SSH transport itself fails (auth, connect, key load, timeout)."""


@dataclass(frozen=True)
class CommandOutcome:
    command: str
    exit_code: int
    stdout: str
    stderr: str


class SshExecutor:
    """Runs whitelisted runbook commands on the Yuki target VM over SSH.

    Only strings produced by runbooks.command_for() may reach run(); caller
    input is never interpolated into shell text anywhere upstream.
    """

    def __init__(
        self,
        host: str,
        user: str,
        key_path: Path,
        connect_timeout_seconds: float = 10.0,
        command_timeout_seconds: float = 30.0,
    ) -> None:
        self.host = host
        self.user = user
        self.key_path = key_path
        self.connect_timeout_seconds = connect_timeout_seconds
        self.command_timeout_seconds = command_timeout_seconds

    @classmethod
    def from_settings(cls, settings: Settings) -> "SshExecutor":
        if not settings.target_ssh_host:
            raise SshNotConfiguredError("POCKETSRE_TARGET_SSH_HOST is not configured.")
        if not settings.target_ssh_key_path.is_file():
            raise SshNotConfiguredError(
                f"SSH key not found at {settings.target_ssh_key_path}."
            )
        return cls(
            host=settings.target_ssh_host,
            user=settings.target_ssh_user,
            key_path=settings.target_ssh_key_path,
            connect_timeout_seconds=settings.ssh_connect_timeout_seconds,
            command_timeout_seconds=settings.ssh_command_timeout_seconds,
        )

    def run(self, command: str) -> CommandOutcome:
        """Execute one whitelisted command and capture exit code + both streams."""
        try:
            pkey = paramiko.Ed25519Key.from_private_key_file(str(self.key_path))
        except Exception as exc:
            raise SshExecutionError(f"Cannot load SSH key {self.key_path}: {exc}") from exc

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(
                hostname=self.host,
                username=self.user,
                pkey=pkey,
                timeout=self.connect_timeout_seconds,
                banner_timeout=self.connect_timeout_seconds,
                auth_timeout=self.connect_timeout_seconds,
            )
        except (socket.timeout, paramiko.SSHException, OSError) as exc:
            raise SshExecutionError(f"SSH connect to {self.host} failed: {exc}") from exc

        try:
            _, stdout, stderr = client.exec_command(command, timeout=self.command_timeout_seconds)
            out = stdout.read().decode("utf-8", errors="replace")
            err = stderr.read().decode("utf-8", errors="replace")
            return CommandOutcome(
                command=command,
                exit_code=stdout.channel.recv_exit_status(),
                stdout=out,
                stderr=err,
            )
        except (socket.timeout, paramiko.SSHException) as exc:
            raise SshExecutionError(f"Command timed out or transport failed: {exc}") from exc
        finally:
            client.close()
