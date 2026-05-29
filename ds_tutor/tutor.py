"""核心调度逻辑 — 串联 CLI、Prompt 引擎、记忆库"""

import os
from pathlib import Path

from . import cli
from .prompt_engine import explain, analyze_code, generate_practice, get_hint
from .memory import (
    record_error,
    get_all_errors,
    check_warnings,
    get_weak_points_summary,
    get_stats,
    mark_mastered,
)
from .config import load_config, save_config, get_api_key


# ── 上一次分析上下文（用于 hint 追问）──
_last_context = {"code": "", "problem": "", "category": ""}


def handle_explain(args: str):
    """处理 explain 命令"""
    if not args.strip():
        cli.console.print("[red]用法: explain <知识点>[/red]")
        return

    topic = args.strip()
    cli.print_status(f"正在生成「{topic}」的可视化讲解...")
    try:
        result = explain(topic)
        cli.render_markdown(result)
    except Exception as e:
        cli.console.print(f"[red]错误: {e}[/red]")


def handle_analyze(args: str):
    """处理 analyze 命令"""
    if not args.strip():
        cli.console.print("[red]用法: analyze <代码文件路径>[/red]")
        return

    filepath = Path(args.strip())
    if not filepath.exists():
        cli.console.print(f"[red]文件不存在: {filepath}[/red]")
        return

    code = filepath.read_text(encoding="utf-8")
    cli.print_status(f"已读取代码文件 ({len(code)} 字符)")

    # 获取题目描述
    cli.console.print()
    problem_desc = cli.get_multiline_input("请输入题目描述（可选）:")
    cli.console.print()

    # 检测题目类型（简易关键词匹配）
    category = _detect_category(code, problem_desc)

    # 获取历史预警
    warnings = check_warnings(category)
    memory_text = ""
    if warnings:
        cli.render_warning_box(
            f"你之前在 [{category}] 类型题目中有 {len(warnings)} 个重复错误模式，请在分析中注意。"
        )
        memory_text = get_weak_points_summary()

    # 调用 LLM 分析
    cli.print_status("正在进行代码分析...")
    try:
        result = analyze_code(code, problem_desc, memory_text)
        cli.render_markdown(result)

        # 保存上下文
        _last_context["code"] = code
        _last_context["problem"] = problem_desc
        _last_context["category"] = category

        # 询问是否记录错误
        cli.console.print()
        if cli.Confirm.ask("是否需要记录本次错误到记忆库？", default=False):
            _interactive_record_error(category)

    except Exception as e:
        cli.console.print(f"[red]分析失败: {e}[/red]")


def handle_hint():
    """处理 hint 命令 — 请求更多提示"""
    if not _last_context["code"]:
        cli.console.print("[dim]没有上一次的分析上下文，请先使用 'analyze' 命令[/dim]")
        return

    cli.print_status("获取更进一步的提示...")
    try:
        result = get_hint()
        cli.render_markdown(result)
    except Exception as e:
        cli.console.print(f"[red]错误: {e}[/red]")


def handle_practice(args: str):
    """处理 practice 命令"""
    category = args.strip()
    weak_points = get_weak_points_summary()

    if category:
        # 查该类别的高频错误
        from .memory import get_frequent_patterns

        patterns = [p for p in get_frequent_patterns(min_count=1) if p["category"] == category]
        if patterns:
            weak_points = f"重点关注 [{category}] 类型:\n"
            for p in patterns:
                weak_points += f"- {p['error_type']}: 已出现 {p['cnt']} 次\n"
        else:
            weak_points = f"学生想练习 [{category}] 类型的题目"

    cli.print_status("正在生成针对性练习题...")
    try:
        result = generate_practice(weak_points)
        cli.render_markdown(result)
    except Exception as e:
        cli.console.print(f"[red]错误: {e}[/red]")


def handle_memory():
    """处理 memory 命令 — 展示错误记忆"""
    errors = get_all_errors()
    if not errors:
        cli.console.print("  [dim]🎉 错误记忆库为空，继续保持！[/dim]")
        return

    cli.render_error_memory(errors)

    from .memory import get_frequent_patterns

    patterns = get_frequent_patterns(min_count=2)
    if patterns:
        cli.console.print()
        cli.console.print("[bold yellow]🔁 高频重复错误 (>1次):[/bold yellow]")
        for p in patterns:
            cli.console.print(
                f"  [{p['category']}] {p['error_type']} — 已出现 [red]{p['cnt']} 次[/red]"
            )

    cli.console.print()
    if cli.Confirm.ask("是否有错误类型已掌握，标记为已解决？", default=False):
        error_type = cli.Prompt.ask("请输入要标记的错误类型")
        mark_mastered(error_type)
        cli.print_status(f"已标记 [{error_type}] 为已掌握", cli.SUCCESS)


def handle_stats():
    """处理 stats 命令 — 展示学习统计"""
    stats = get_stats()
    cli.console.print()
    cli.render_panel(
        f"📚 学习次数: {stats['total_sessions']}\n"
        f"🐛 累计错误: {stats['total_errors']}\n"
        f"✅ 已掌握类型: {stats['mastered']}\n"
        f"🔧 待解决类型: {stats['unmastered']}",
        title="学习统计",
        style=cli.ACCENT,
    )


def handle_config():
    """处理 config 命令 — 配置 API Key"""
    config = load_config()

    cli.console.print()
    cli.console.print("[bold]当前配置:[/bold]")
    cli.console.print(f"  API Base: {config.get('api_base', 'https://api.openai.com/v1')}")
    cli.console.print(f"  Model: {config.get('model', 'gpt-4o')}")
    has_key = bool(get_api_key())
    cli.console.print(f"  API Key: {'已设置' if has_key else '[red]未设置[/red]'}")

    cli.console.print()
    if cli.Confirm.ask("是否修改配置？", default=False):
        api_key = cli.Prompt.ask("API Key", password=True)
        if api_key.strip():
            config["api_key"] = api_key
        api_base = cli.Prompt.ask("API Base", default=config.get("api_base", "https://api.openai.com/v1"))
        config["api_base"] = api_base
        model = cli.Prompt.ask("Model", default=config.get("model", "gpt-4o"))
        config["model"] = model
        save_config(config)
        cli.print_status("配置已保存", cli.SUCCESS)


def _detect_category(code: str, problem_desc: str) -> str:
    """简易检测题目/代码类型"""
    text = (code + problem_desc).lower()
    keywords = {
        "dp": ["dp", "动态规划", "状态转移", "memo", "memoization"],
        "graph": ["graph", "图", "dfs", "bfs", "dijkstra", "拓扑", "连通", "最短"],
        "tree": ["tree", "树", "二叉树", "bst", "segment tree", "线段树", "trie"],
        "greedy": ["greedy", "贪心"],
        "math": ["math", "数学", "素数", "gcd", "快速幂", "mod", "数论"],
        "string": ["string", "字符串", "kmp", "trie", "回文", "后缀"],
        "data_structure": ["stack", "queue", "heap", "栈", "队列", "堆", "优先队列"],
    }
    for cat, kws in keywords.items():
        if any(kw in text for kw in kws):
            return cat
    return "general"


def _interactive_record_error(category: str):
    """交互式记录错误"""
    error_type = cli.Prompt.ask("错误类型", default="逻辑错误")
    desc = cli.Prompt.ask("错误描述（简短）")
    record_error(category, error_type, desc)
    cli.print_status("已记录到错误记忆库", cli.SUCCESS)
