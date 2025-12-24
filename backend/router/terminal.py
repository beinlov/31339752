import platform
import subprocess
import os
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

class CommandRequest(BaseModel):
    command: str
    cwd: Optional[str] = None
    timeout_seconds: Optional[int] = 300  # 默认5分钟超时

class CommandResponse(BaseModel):
    status: str
    stdout: str
    stderr: str
    return_code: int

@router.post("/terminal/exec", response_model=CommandResponse)
async def exec_command(req: CommandRequest):
    """
    执行PowerShell命令 - 无任何限制
    直接在服务器上执行任意PowerShell命令
    """
    cmd = (req.command or '').strip()
    if not cmd:
        raise HTTPException(status_code=400, detail="Command cannot be empty")

    # 平台适配 - 直接执行，无任何命令过滤
    is_windows = platform.system().lower().startswith('win')
    if is_windows:
        # 使用 PowerShell 执行命令，无任何限制
        # 设置输出编码为 UTF-8
        full_cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", 
                    f"[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; {cmd}"]
    else:
        # Linux/Mac 使用 bash
        full_cmd = ["/bin/bash", "-lc", cmd]

    try:
        # 设置环境变量确保 UTF-8 编码
        env = os.environ.copy()
        if is_windows:
            env['PYTHONIOENCODING'] = 'utf-8'
        
        proc = subprocess.run(
            full_cmd,
            cwd=req.cwd or None,
            capture_output=True,
            timeout=max(1, int(req.timeout_seconds or 300)),
            env=env,
            encoding='utf-8',
            errors='replace'  # 遇到无法解码的字符时替换而不是报错
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
