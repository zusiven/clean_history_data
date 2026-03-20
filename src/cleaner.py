import errno
import stat
import time
import logging
from dataclasses import dataclass, field
from pathlib import Path
from wztools import error_info

logger = logging.getLogger("")


@dataclass
class CleanResult:
    deleted_files: list[Path] = field(default_factory=list)
    deleted_dirs:  list[Path] = field(default_factory=list)
    skipped_files: list[Path] = field(default_factory=list)

    @property
    def summary(self) -> str:
        return (
            f"删除 {len(self.deleted_files)} 个文件, "
            f"{len(self.deleted_dirs)} 个空目录, "
            f"保留 {len(self.skipped_files)} 个文件"
        )


def _format_duration(seconds: float) -> str:
    seconds = int(seconds)
    days    = seconds // 86400
    hours   = (seconds % 86400) // 3600
    mins    = (seconds % 3600) // 60
    secs    = seconds % 60

    parts = []
    if days:  parts.append(f"{days} 天")
    if hours: parts.append(f"{hours} 小时")
    if mins:  parts.append(f"{mins} 分")
    if secs:  parts.append(f"{secs} 秒")
    return " ".join(parts) or "0 秒"


def delete_old_files_and_empty_dirs(folder_path: str, expire_seconds: float) -> CleanResult:
    folder = Path(folder_path)
    current_time = time.time()

    logger.info(f"  ┌─ 目录: {folder}")
    logger.info(f"  ├─ 阈值: {_format_duration(expire_seconds)}")

    result = CleanResult()
    _delete_expired_files(folder, current_time, expire_seconds, result)
    _delete_empty_dirs(folder, result)

    logger.info(f"  └─ {result.summary}")

    return result


def _delete_expired_files(
    folder: Path,
    current_time: float,
    expire_seconds: float,
    result: CleanResult,
) -> None:
    for file in folder.rglob("*"):
        try:
            st = file.lstat()

            if stat.S_ISDIR(st.st_mode):
                continue

            if current_time - st.st_mtime > expire_seconds:
                file.unlink()
                result.deleted_files.append(file)
            else:
                result.skipped_files.append(file)

        except Exception:
            logger.error(f"  ✗ 删除文件失败: {file}\n{error_info(show_details=True)}")


def _delete_empty_dirs(folder: Path, result: CleanResult) -> None:
    for dir_path in sorted(folder.rglob("*"), reverse=True):
        if not dir_path.is_dir():
            continue
        if not dir_path.is_relative_to(folder) or dir_path == folder:
            continue
        try:
            dir_path.rmdir()
            result.deleted_dirs.append(dir_path)
        except OSError as e:
            if e.errno == errno.ENOTEMPTY:
                pass
            else:
                logger.error(f"  ✗ 删除目录失败: {dir_path} — {e}")