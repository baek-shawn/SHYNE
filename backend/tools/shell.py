"""셸 실행 도구: run_command.

`base_dir`을 작업 디렉터리로 해서 OS 기본 셸(Windows는 cmd.exe, 그 외는 /bin/sh)로 명령을
실행한다. `timeout`(Agent Loop의 command_timeout)을 넘기면 자식 프로세스까지 포함해 강제
종료한다. Step 4에서 BLOCK 목록(rm -rf, shutdown, format, sudo, git push --force 등)을 이
모듈에 연결할 예정이다.
"""

from __future__ import annotations

import locale
import os
import signal
import subprocess
from pathlib import Path

from tools.registry import ToolResult

DEFAULT_TIMEOUT = 60
MAX_OUTPUT_CHARS = 10_000


def _decode_output(data: bytes) -> str:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        # cmd.exe 내장 명령이나 일부 Windows 프로그램은 OS 기본 인코딩(cp949 등)으로 출력한다.
        text = data.decode(locale.getpreferredencoding(False), errors="replace")
    return text.replace("\r\n", "\n")


def _truncate(text: str) -> str:
    """출력이 너무 길면 앞부분과 뒷부분만 남긴다 (오류 메시지는 보통 끝에 있다)."""
    if len(text) <= MAX_OUTPUT_CHARS:
        return text
    head = MAX_OUTPUT_CHARS // 4
    tail = MAX_OUTPUT_CHARS - head
    omitted = len(text) - MAX_OUTPUT_CHARS
    return f"{text[:head]}\n[... {omitted}자 생략 ...]\n{text[-tail:]}"


def _kill_process_tree(process: subprocess.Popen) -> None:
    """셸이 띄운 자식 프로세스까지 함께 종료한다.

    `shell=True`에서는 process가 셸 자체라서, 셸만 죽이면 실제 명령(python 등)이 살아남아
    출력 파이프를 붙잡고 있을 수 있다.
    """
    if process.poll() is not None:
        return
    try:
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(process.pid)],
                capture_output=True,
                check=False,
            )
        else:
            os.killpg(process.pid, signal.SIGKILL)
    except (OSError, ProcessLookupError):
        pass
    if process.poll() is None:
        process.kill()


def _format_output(exit_code: int | None, stdout: str, stderr: str) -> str:
    parts = [f"exit_code: {exit_code if exit_code is not None else '(없음)'}"]
    if stdout.strip():
        parts.append(f"[stdout]\n{_truncate(stdout.rstrip())}")
    if stderr.strip():
        parts.append(f"[stderr]\n{_truncate(stderr.rstrip())}")
    if len(parts) == 1:
        parts.append("(출력 없음)")
    return "\n".join(parts)


def run_command(arguments: dict, *, base_dir: Path, timeout: int = DEFAULT_TIMEOUT) -> ToolResult:
    command = arguments.get("command")
    if not isinstance(command, str) or not command.strip():
        return ToolResult(False, "", "command는 비어 있지 않은 문자열이어야 합니다.")

    env = os.environ.copy()
    # 출력을 파이프로 받으면 Windows의 Python은 cp949로 인코딩해서, 터미널에서는 잘 되던
    # 이모지/특수문자 print가 UnicodeEncodeError로 실패한다. 자식 Python은 UTF-8로 출력하게 한다.
    env.setdefault("PYTHONIOENCODING", "utf-8")

    popen_kwargs: dict = {}
    if os.name != "nt":
        popen_kwargs["start_new_session"] = True  # timeout 시 프로세스 그룹 전체를 종료하기 위함

    try:
        process = subprocess.Popen(
            command,
            shell=True,
            cwd=base_dir,
            env=env,
            stdin=subprocess.DEVNULL,  # 입력을 기다리는 명령이 멈춰 있지 않게 한다.
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            **popen_kwargs,
        )
    except OSError as exc:
        return ToolResult(False, "", f"명령을 실행하지 못했습니다: {exc}")

    timed_out = False
    try:
        stdout_bytes, stderr_bytes = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        _kill_process_tree(process)
        try:
            stdout_bytes, stderr_bytes = process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            stdout_bytes, stderr_bytes = b"", b""
    except BaseException:
        # Ctrl+C 등으로 중단될 때 실행 중이던 명령을 남겨두지 않는다.
        _kill_process_tree(process)
        raise

    stdout = _decode_output(stdout_bytes or b"")
    stderr = _decode_output(stderr_bytes or b"")

    if timed_out:
        return ToolResult(
            False,
            _format_output(None, stdout, stderr),
            f"명령이 {timeout}초 안에 끝나지 않아 강제 종료했습니다.",
        )

    output = _format_output(process.returncode, stdout, stderr)
    if process.returncode != 0:
        return ToolResult(False, output, f"명령이 종료 코드 {process.returncode}로 실패했습니다.")
    return ToolResult(True, output)
