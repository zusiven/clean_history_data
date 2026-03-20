import datetime as dt
from pathlib import Path

from mlog_util import get_logger, MultiProcessSafeSizeRotatingHandler

from src.cleaner import delete_old_files_and_empty_dirs
from config.clean_list import directories

# 日志配置
multi_handler = MultiProcessSafeSizeRotatingHandler(filename="logs/clean.log", backupCount=7)
logger = get_logger("", custom_handlers=multi_handler)


def main():
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total = len(directories)

    logger.info("=" * 50)
    logger.info(f"  历史文件清理开始")
    logger.info(f"  时间: {now}  共 {total} 个目录")
    logger.info("=" * 50)

    success, skipped, failed = 0, 0, 0

    for i, (directory_path, expire_seconds) in enumerate(directories.items(), 1):
        logger.info(f"[{i}/{total}]")
        path = Path(directory_path)

        if not path.exists():
            logger.warning(f"  ⚠ 目录不存在，跳过: {directory_path}")
            skipped += 1
            continue

        if not path.is_dir():
            logger.warning(f"  ⚠ 路径不是目录，跳过: {directory_path}")
            skipped += 1
            continue

        try:
            delete_old_files_and_empty_dirs(directory_path, expire_seconds)
            success += 1
        except Exception:
            logger.exception(f"  ✗ 清理异常: {directory_path}")
            failed += 1

    logger.info("=" * 50)
    logger.info(f"  清理完成")
    logger.info(f"  ✔ 成功 {success}  ⚠ 跳过 {skipped}  ✗ 失败 {failed}")
    logger.info(f"  时间: {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 50)


if __name__ == "__main__":
    main()