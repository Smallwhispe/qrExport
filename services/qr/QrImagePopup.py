"""二维码图片弹出管理。
核心思路:
  1) 生成新 QR 图之前: 关掉上一次弹出的图片查看进程
  2) Windows 不使用 `start`(它是 cmd 内置命令,
     启动后就结束, 实际看图软件是另一个进程,
     Popen 跟踪不到), 改用系统自带的 mspaint /
     rundll32 shimgvw.dll, 或用户指定的 viewer。
"""
import logging
import os
import platform
import subprocess
import threading
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_last_process: Optional[subprocess.Popen] = None


# --------------------------------------------------------------------------
# 系统相关
# --------------------------------------------------------------------------
def _os_name() -> str:
    return platform.system().lower()


def _pick_default_viewer() -> Tuple[str, bool]:
    """返回 (viewer_command, use_shell)。

    - windows: 优先 mspaint (自带, 稳定, Popen 能跟踪到进程);
               若希望用图片查看器 (Photo Viewer) 可在 .env 里写:
               QR_IMAGE_VIEWER=rundll32 "C:\\Windows\\System32\\shimgvw.dll,ImageView_Fullscreen"
    - darwin : open
    - linux  : xdg-open
    """
    name = _os_name()
    if name == "windows":
        return "mspaint", False
    if name == "darwin":
        return "open", False
    return "xdg-open", False


def _build_cmd(viewer: str, filepath: str) -> Tuple[list, bool]:
    """根据 viewer 构造 Popen 参数, 返回 (cmd_list, use_shell)。

    约定:
      - 空 / 'start' / 'default' -> 走 _pick_default_viewer()
      - 其它按用户原样调用, 支持带参数, 例如:
          QR_IMAGE_VIEWER=rundll32 "C:\\Windows\\System32\\shimgvw.dll,ImageView_Fullscreen"
    """
    if not viewer or viewer.strip().lower() in ("start", "default"):
        default_viewer, use_shell = _pick_default_viewer()
        return _build_cmd(default_viewer, filepath)

    # 支持用户在 viewer 里写空格分隔的参数
    # 用 shlex 风格手工切: 双引号包裹的视为一整段
    parts = _split_with_quotes(viewer)
    parts.append(filepath)
    # 对 shell 内置命令 (如 `echo xxx`) 才需要 shell=True, 这里默认 False
    return parts, False


def _split_with_quotes(s: str) -> list:
    """按空格拆分字符串, 双引号内的内容保留为整体。"""
    result = []
    buf = []
    in_quote = False
    for ch in s:
        if ch == '"':
            in_quote = not in_quote
            continue
        if ch == ' ' and not in_quote:
            if buf:
                result.append(''.join(buf))
                buf = []
            continue
        buf.append(ch)
    if buf:
        result.append(''.join(buf))
    return result


# --------------------------------------------------------------------------
# 清理 / 弹出
# --------------------------------------------------------------------------
def _kill_previous_popup() -> None:
    global _last_process
    if _last_process is None:
        return
    proc: subprocess.Popen = _last_process
    _last_process = None
    try:
        if proc.poll() is None:
            logger.info("[qr popup] - 关闭上一次的图片查看进程 pid=%s", proc.pid)
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                try:
                    proc.kill()
                    proc.wait(timeout=3)
                except Exception:
                    pass
    except Exception as e:
        logger.warning("[qr popup] - 关闭旧图片查看进程失败: %s", e)


def popup_image(filepath: str, viewer_command: Optional[str] = None) -> None:
    if not filepath or not os.path.exists(filepath):
        raise FileNotFoundError(f"图片文件不存在: {filepath}")

    with _lock:
        # 先关旧窗口
        _kill_previous_popup()

        viewer = (viewer_command or "").strip()
        if not viewer or viewer.lower() in ("start", "default"):
            viewer, _ = _pick_default_viewer()

        cmd, use_shell = _build_cmd(viewer, filepath)

        logger.info("[qr popup] - 打开二维码图片: %s (viewer=%s)", filepath, " ".join(cmd))

        try:
            proc = subprocess.Popen(
                cmd,
                shell=use_shell,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            global _last_process
            _last_process = proc
        except Exception as e:
            logger.exception("[qr popup] - 弹出图片失败: %s", e)
            raise

