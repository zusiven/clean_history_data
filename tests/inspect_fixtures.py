"""
手动检查工具：创建 fixtures → 检查 → 运行清理 → 验证结果 → 清理
用法：uv run python tests/inspect_fixtures.py
"""
import os
import time
import shutil
from pathlib import Path

from src.cleaner import delete_old_files_and_empty_dirs
from config.clean_list import directories

FIXTURES = Path("tests/fixtures")


# ── 工具函数 ─────────────────────────────────────────────────────

def make_file(path: Path, content: str = "test") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return path


def make_expired_file(path: Path) -> Path:
    make_file(path)
    expired = time.time() - 10
    os.utime(path, (expired, expired))
    return path


def expire_symlink(link: Path) -> None:
    expired = time.time() - 10
    os.utime(link, (expired, expired), follow_symlinks=False)


def print_tree(base: Path, prefix: str = "") -> None:
    entries = sorted(base.iterdir(), key=lambda p: (p.is_file(), p.name))
    for i, entry in enumerate(entries):
        connector = "└─" if i == len(entries) - 1 else "├─"
        if entry.is_symlink():
            target = os.readlink(entry)
            print(f"{prefix}{connector} {entry.name} -> {target}  [symlink]")
        elif entry.is_dir():
            print(f"{prefix}{connector} {entry.name}/")
            extension = "   " if i == len(entries) - 1 else "│  "
            print_tree(entry, prefix + extension)
        else:
            mtime = entry.stat().st_mtime
            age   = time.time() - mtime
            print(f"{prefix}{connector} {entry.name}  (age: {age:.1f}s)")


# ── 主流程 ───────────────────────────────────────────────────────

def create_fixtures() -> None:
    print("▶ 创建 fixtures...\n")

    make_expired_file(FIXTURES / "expired" / "old.txt")
    make_file(FIXTURES / "recent" / "new.txt")
    make_expired_file(FIXTURES / "nested_clean" / "level1" / "level2" / "old.txt")
    make_file(FIXTURES / "nested_keep" / "level1" / "level2" / "keep.txt")
    make_expired_file(FIXTURES / "mixed" / "old.txt")
    make_file(FIXTURES / "mixed" / "new.txt")

    target = make_file(FIXTURES / "symlink" / "real.txt")
    link = FIXTURES / "symlink" / "link.txt"
    link.symlink_to(target)
    expire_symlink(link)

    ghost = FIXTURES / "dangling" / "ghost.txt"
    link  = FIXTURES / "dangling" / "dangling.txt"
    (FIXTURES / "dangling").mkdir(parents=True, exist_ok=True)
    link.symlink_to(ghost)
    expire_symlink(link)

    make_expired_file(FIXTURES / "root_protection" / "old.txt")
    make_file(FIXTURES / "nonempty" / "subdir" / "keep.txt")
    (FIXTURES / "empty_dir" / "empty_subdir").mkdir(parents=True, exist_ok=True)
    make_expired_file(FIXTURES / "empty_dir" / "old.txt")

    print("fixtures 目录结构：\n")
    print_tree(FIXTURES)


def run_clean() -> None:
    print("\n▶ 运行清理...\n")
    for path, expire_seconds in directories.items():
        if not Path(path).exists():
            continue
        result = delete_old_files_and_empty_dirs(path, expire_seconds)
        print(f"  {path}")
        print(f"    删除文件: {[f.name for f in result.deleted_files]}")
        print(f"    删除目录: {[d.name for d in result.deleted_dirs]}")
        print(f"    保留文件: {[f.name for f in result.skipped_files]}")


def main():
    if FIXTURES.exists():
        shutil.rmtree(FIXTURES)

    # 第一阶段：创建
    create_fixtures()
    input("\n[1/2] 去 tests/fixtures/ 检查文件结构，确认后按 Enter 运行清理...")

    # 第二阶段：清理
    run_clean()
    print("\n清理后目录结构：\n")
    print_tree(FIXTURES)
    input("\n[2/2] 去 tests/fixtures/ 验证清理结果，确认后按 Enter 删除 fixtures...")

    # 第三阶段：收尾
    shutil.rmtree(FIXTURES)
    print("\n✔ fixtures 已删除，完成。")


if __name__ == "__main__":
    main()