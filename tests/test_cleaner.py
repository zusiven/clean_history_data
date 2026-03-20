import os
import time
import shutil
import pytest
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


# ── pytest fixture ───────────────────────────────────────────────

@pytest.fixture(autouse=True)
def setup_fixtures():
    # 1. expired
    make_expired_file(FIXTURES / "expired" / "old.txt")

    # 2. recent
    make_file(FIXTURES / "recent" / "new.txt")

    # 3. nested_clean
    make_expired_file(FIXTURES / "nested_clean" / "level1" / "level2" / "old.txt")

    # 4. nested_keep
    make_file(FIXTURES / "nested_keep" / "level1" / "level2" / "keep.txt")

    # 5. mixed
    make_expired_file(FIXTURES / "mixed" / "old.txt")
    make_file(FIXTURES / "mixed" / "new.txt")

    # 6. symlink
    target = make_file(FIXTURES / "symlink" / "real.txt")
    link = FIXTURES / "symlink" / "link.txt"
    if not link.exists():
        link.symlink_to(target)
    expire_symlink(link)

    # 7. dangling
    ghost = FIXTURES / "dangling" / "ghost.txt"
    link  = FIXTURES / "dangling" / "dangling.txt"
    (FIXTURES / "dangling").mkdir(parents=True, exist_ok=True)
    if not link.exists():
        link.symlink_to(ghost)
    expire_symlink(link)

    # 8. root_protection
    make_expired_file(FIXTURES / "root_protection" / "old.txt")

    # 9. nonempty
    make_file(FIXTURES / "nonempty" / "subdir" / "keep.txt")

    # 10. empty_dir
    (FIXTURES / "empty_dir" / "empty_subdir").mkdir(parents=True, exist_ok=True)
    make_expired_file(FIXTURES / "empty_dir" / "old.txt")

    yield

    if FIXTURES.exists():
        shutil.rmtree(FIXTURES)


# ── 测试 ─────────────────────────────────────────────────────────

# 1. 过期文件被删除，且只删了这一个
def test_deletes_expired_file():
    result = delete_old_files_and_empty_dirs(
        "tests/fixtures/expired",
        directories["tests/fixtures/expired"],
    )
    assert FIXTURES / "expired" / "old.txt" in result.deleted_files
    assert len(result.deleted_files) == 1
    assert len(result.skipped_files) == 0


# 2. 未过期文件保留，且没有任何文件被删
def test_keeps_recent_file():
    result = delete_old_files_and_empty_dirs(
        "tests/fixtures/recent",
        directories["tests/fixtures/recent"],
    )
    assert FIXTURES / "recent" / "new.txt" in result.skipped_files
    assert len(result.deleted_files) == 0
    assert len(result.skipped_files) == 1


# 3. 嵌套目录文件全部过期：文件删除，子目录逐层清空后被删
def test_nested_dir_all_expired_cleaned():
    result = delete_old_files_and_empty_dirs(
        "tests/fixtures/nested_clean",
        directories["tests/fixtures/nested_clean"],
    )
    assert FIXTURES / "nested_clean" / "level1" / "level2" / "old.txt" in result.deleted_files
    assert FIXTURES / "nested_clean" / "level1" / "level2" in result.deleted_dirs
    assert FIXTURES / "nested_clean" / "level1" in result.deleted_dirs
    assert len(result.deleted_files) == 1
    assert len(result.deleted_dirs) == 2


# 4. 嵌套目录有未过期文件：文件保留，目录不被删
def test_nested_dir_with_recent_file_kept():
    result = delete_old_files_and_empty_dirs(
        "tests/fixtures/nested_keep",
        directories["tests/fixtures/nested_keep"],
    )
    assert FIXTURES / "nested_keep" / "level1" / "level2" / "keep.txt" in result.skipped_files
    assert len(result.deleted_files) == 0
    assert len(result.deleted_dirs) == 0


# 5. 混合场景：只删过期文件，保留未过期文件
def test_mixed_files():
    result = delete_old_files_and_empty_dirs(
        "tests/fixtures/mixed",
        directories["tests/fixtures/mixed"],
    )
    assert FIXTURES / "mixed" / "old.txt" in result.deleted_files
    assert FIXTURES / "mixed" / "new.txt" in result.skipped_files
    assert len(result.deleted_files) == 1
    assert len(result.skipped_files) == 1


# 6. symlink：只删链接，目标文件在 skipped 里
def test_symlink_deletes_link_not_target():
    result = delete_old_files_and_empty_dirs(
        "tests/fixtures/symlink",
        directories["tests/fixtures/symlink"],
    )
    assert FIXTURES / "symlink" / "link.txt" in result.deleted_files
    assert FIXTURES / "symlink" / "real.txt" in result.skipped_files
    assert len(result.deleted_files) == 1
    assert len(result.skipped_files) == 1


# 7. 悬空 symlink：链接被删，deleted_files 只有这一个
def test_dangling_symlink_deleted():
    result = delete_old_files_and_empty_dirs(
        "tests/fixtures/dangling",
        directories["tests/fixtures/dangling"],
    )
    assert FIXTURES / "dangling" / "dangling.txt" in result.deleted_files
    assert len(result.deleted_files) == 1
    assert len(result.skipped_files) == 0


# 8. 根目录本身不在 deleted_dirs 里
def test_root_dir_not_deleted():
    result = delete_old_files_and_empty_dirs(
        "tests/fixtures/root_protection",
        directories["tests/fixtures/root_protection"],
    )
    assert FIXTURES / "root_protection" not in result.deleted_dirs
    assert (FIXTURES / "root_protection").exists()


# 9. 非空目录不在 deleted_dirs 里
def test_keeps_nonempty_dir():
    result = delete_old_files_and_empty_dirs(
        "tests/fixtures/nonempty",
        directories["tests/fixtures/nonempty"],
    )
    assert FIXTURES / "nonempty" / "subdir" not in result.deleted_dirs
    assert len(result.deleted_dirs) == 0
    assert len(result.deleted_files) == 0


# 10. 过期文件删除后，空目录被清理
def test_deletes_empty_dir_after_file_removal():
    result = delete_old_files_and_empty_dirs(
        "tests/fixtures/empty_dir",
        directories["tests/fixtures/empty_dir"],
    )
    assert FIXTURES / "empty_dir" / "old.txt" in result.deleted_files
    assert FIXTURES / "empty_dir" / "empty_subdir" in result.deleted_dirs
    assert len(result.deleted_files) == 1
    assert len(result.deleted_dirs) == 1