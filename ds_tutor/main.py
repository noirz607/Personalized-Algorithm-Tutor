"""CLI 入口 — 个性化算法学习助手"""

import sys
from rich.prompt import Prompt

from . import cli
from .tutor import (
    handle_explain,
    handle_analyze,
    handle_hint,
    handle_practice,
    handle_memory,
    handle_stats,
    handle_config,
)
from .config import get_api_key


def ensure_config() -> bool:
    """确保已配置 API Key，未配置则引导配置"""
    if get_api_key():
        return True
    cli.console.print()
    cli.console.print("[red]未检测到 API Key，请先配置[/red]")
    handle_config()
    return bool(get_api_key())


def main():
    cli.print_banner()

    if not ensure_config():
        cli.console.print("[red]未配置 API Key，退出。请设置环境变量 OPENAI_API_KEY 或运行 config 命令[/red]")
        sys.exit(1)

    cli.console.print("  输入 [bold]help[/bold] 查看命令，输入 [bold]quit[/bold] 退出")
    cli.console.print()

    while True:
        try:
            raw = Prompt.ask("  [bold cyan]>>>[/bold cyan]")
        except (KeyboardInterrupt, EOFError):
            cli.console.print("\n  再见 👋")
            break

        cmd = raw.strip()
        if not cmd:
            continue

        parts = cmd.split(maxsplit=1)
        action = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        if action in ("quit", "exit", "q"):
            cli.console.print("  再见 👋")
            break
        elif action == "help":
            cli.show_help()
        elif action == "explain":
            handle_explain(args)
        elif action == "analyze":
            handle_analyze(args)
        elif action == "hint":
            handle_hint()
        elif action == "practice":
            handle_practice(args)
        elif action == "memory":
            handle_memory()
        elif action == "stats":
            handle_stats()
        elif action == "config":
            handle_config()
        else:
            cli.console.print(f"  [red]未知命令: {action}[/red]")
            cli.console.print("  输入 [bold]help[/bold] 查看可用命令")

        cli.console.print()


if __name__ == "__main__":
    main()
