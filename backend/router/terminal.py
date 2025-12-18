import platform
import shlex
import subprocess
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

# 简单的危险命令黑名单（可根据需要扩展）
DENY_PATTERNS = [
    'rm -rf', 'shutdown', 'reboot', 'halt', 'poweroff', 'init 0', 'mkfs', 'format',
    ':(){:|:&};:', 'del /Q', 'rd /S', 'rd /S /Q', 'bcdedit', 'diskpart', 'format',
    'shutdown /s', 'shutdown /r', 'shutdown -s', 'shutdown -r'
]

class CommandRequest(BaseModel):
    command: str
    cwd: Optional[str] = None
    timeout_seconds: Optional[int] = 10

class CommandResponse(BaseModel):
    status: str
    stdout: str
    stderr: str
    return_code: int

@router.post("/terminal/exec", response_model=CommandResponse)
async def exec_command(req: CommandRequest):
    cmd = (req.command or '').strip()
    if not cmd:
        raise HTTPException(status_code=400, detail="Command cannot be empty")

    lowered = cmd.lower()
    for pattern in DENY_PATTERNS:
        if pattern in lowered:
            raise HTTPException(status_code=400, detail=f"Command contains forbidden pattern: {pattern}")

    # 平台适配
    is_windows = platform.system().lower().startswith('win')
    if is_windows:
        # 使用 PowerShell 以获得更好的体验
        full_cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", cmd]
    else:
        full_cmd = ["/bin/bash", "-lc", cmd]

    try:
        proc = subprocess.run(
            full_cmd,
            cwd=req.cwd or None,
            capture_output=True,
            text=True,
            timeout=max(1, int(req.timeout_seconds or 10))
        )
        return CommandResponse(
            status="success" if proc.returncode == 0 else "error",
            stdout=proc.stdout or "",
            stderr=proc.stderr or "",
            return_code=proc.returncode
        )
    except subprocess.TimeoutExpired as e:
        raise HTTPException(status_code=408, detail=f"Command timeout after {req.timeout_seconds}s")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
