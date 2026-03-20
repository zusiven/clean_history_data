from datetime import timedelta

DAY  = timedelta(days=1).total_seconds()
WEEK = timedelta(weeks=1).total_seconds()

directories = {
    "tests/fixtures/expired"         : 1,      # 过期阈值 1 秒，测试用
    "tests/fixtures/recent"          : 9999,   # 未过期，测试用
    "tests/fixtures/nested_clean"    : 1,      # 嵌套目录全过期，测试用
    "tests/fixtures/nested_keep"     : 9999,   # 嵌套目录有未过期文件，测试用
    "tests/fixtures/mixed"           : 1,      # 混合场景，测试用
    "tests/fixtures/symlink"         : 1,      # symlink 场景，测试用
    "tests/fixtures/dangling"        : 1,      # 悬空 symlink，测试用
    "tests/fixtures/root_protection" : 1,      # 根目录保护，测试用
    "tests/fixtures/nonempty"        : 9999,   # 非空目录保护，测试用
    "tests/fixtures/empty_dir"       : 1,      # 空目录清理，测试用
}

    