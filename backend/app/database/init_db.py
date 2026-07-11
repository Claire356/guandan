"""数据库初始化命令：python -m app.database.init_db。"""

from .sqlite import DATABASE_PATH, init_db


def main() -> None:
    """创建缺失的数据表并输出数据库位置。"""
    init_db()
    print(f"数据库初始化完成: {DATABASE_PATH}")


if __name__ == "__main__":
    main()
