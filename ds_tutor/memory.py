"""个人错误记忆库 — 基于 SQLite 的本地存储

记录、查询、预警用户的高频错误模式，实现真正个性化的学习反馈。
"""

import sqlite3
from datetime import datetime
from .config import DB_PATH, CONFIG_DIR


def _get_conn() -> sqlite3.Connection:
    """获取数据库连接，自动创建表"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS errors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            time TEXT NOT NULL,
            category TEXT NOT NULL,
            error_type TEXT NOT NULL,
            description TEXT NOT NULL,
            mastered INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    return conn


def record_error(category: str, error_type: str, description: str):
    """记录一条错误"""
    conn = _get_conn()
    conn.execute(
        "INSERT INTO errors (time, category, error_type, description) VALUES (?, ?, ?, ?)",
        (datetime.now().strftime("%Y-%m-%d %H:%M"), category, error_type, description),
    )
    conn.commit()
    conn.close()


def get_all_errors(limit: int = 50) -> list:
    """获取所有错误记录"""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM errors WHERE mastered = 0 ORDER BY time DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_frequent_patterns(min_count: int = 2) -> list:
    """获取高频错误模式（出现次数 >= min_count）"""
    conn = _get_conn()
    rows = conn.execute(
        """
        SELECT category, error_type, COUNT(*) as cnt
        FROM errors
        WHERE mastered = 0
        GROUP BY category, error_type
        HAVING cnt >= ?
        ORDER BY cnt DESC
        """,
        (min_count,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def check_warnings(category: str) -> list:
    """根据当前题目类型，检查历史中是否有类似的未掌握错误，返回预警列表"""
    conn = _get_conn()
    rows = conn.execute(
        """
        SELECT DISTINCT category, error_type, description, COUNT(*) as cnt
        FROM errors
        WHERE mastered = 0 AND category = ?
        GROUP BY error_type
        ORDER BY cnt DESC
        """,
        (category,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_weak_points_summary() -> str:
    """生成薄弱点摘要文本，用于 Prompt 注入"""
    patterns = get_frequent_patterns(min_count=1)
    if not patterns:
        return ""
    lines = ["## 学生历史错误记录（请注意预警）\n"]
    for p in patterns:
        lines.append(f"- [{p['category']}] {p['error_type']}：已出现 {p['cnt']} 次")
    return "\n".join(lines)


def get_stats() -> dict:
    """获取学习统计"""
    conn = _get_conn()
    total = conn.execute("SELECT COUNT(*) as n FROM errors").fetchone()["n"]
    mastered = conn.execute(
        "SELECT COUNT(DISTINCT error_type) as n FROM errors WHERE mastered = 1"
    ).fetchone()["n"]
    unmastered = conn.execute(
        "SELECT COUNT(DISTINCT error_type) as n FROM errors WHERE mastered = 0"
    ).fetchone()["n"]
    sessions = conn.execute(
        "SELECT COUNT(DISTINCT time) as n FROM errors"
    ).fetchone()["n"]
    conn.close()
    return {
        "total_errors": total,
        "total_sessions": sessions,
        "mastered": mastered,
        "unmastered": unmastered,
    }


def mark_mastered(error_type: str):
    """将某类错误标记为已掌握"""
    conn = _get_conn()
    conn.execute("UPDATE errors SET mastered = 1 WHERE error_type = ?", (error_type,))
    conn.commit()
    conn.close()


def clear_all():
    """清空所有记录（调试用）"""
    conn = _get_conn()
    conn.execute("DELETE FROM errors")
    conn.commit()
    conn.close()
