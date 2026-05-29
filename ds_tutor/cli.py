"""CLI 交互界面 — 基于 Rich 库，适配视觉化学习风格"""

import re
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from rich.layout import Layout
from rich import box
from rich.prompt import Prompt, Confirm

console = Console()

# ── 配色 ──────────────────────────────────────────
ACCENT = "bold cyan"
WARNING = "bold yellow"
DANGER = "bold red"
SUCCESS = "bold green"
TITLE = "bold white on blue"
SUB = "bold magenta"


def print_banner():
    """启动横幅"""
    banner = r"""
  ╔══════════════════════════════════════╗
  ║    🧠 个性化算法学习助手              ║
  ║    Personalized Algorithm Tutor       ║
  ║    视觉化讲解 · 苏格拉底式提问 · 错题记忆  ║
  ╚══════════════════════════════════════╝
"""
    console.print(banner, style=ACCENT)


def print_status(msg: str, style: str = ACCENT):
    """状态提示"""
    console.print(f"  [{style}]{msg}[/{style}]")


def render_markdown(content: str):
    """渲染 Markdown 内容"""
    md = Markdown(content)
    console.print(md)


def render_code(code: str, language: str = "cpp"):
    """渲染代码块"""
    syntax = Syntax(code, language, theme="monokai", line_numbers=True)
    console.print(syntax)


def render_panel(content: str, title: str = "", style: str = ACCENT):
    """渲染带标题的面板"""
    panel = Panel(content, title=title, border_style=style, padding=(1, 2))
    console.print(panel)


def render_table(headers: list, rows: list, title: str = ""):
    """渲染表格"""
    table = Table(title=title, box=box.ROUNDED)
    for h in headers:
        table.add_column(h, style=ACCENT)
    for row in rows:
        table.add_row(*[str(c) for c in row])
    console.print(table)


def render_warning_box(content: str):
    """渲染警告面板"""
    panel = Panel(
        f"⚠️  {content}",
        title="记忆提醒",
        border_style=WARNING,
        padding=(1, 2),
    )
    console.print(panel)


def render_question(question: str, options: list = None):
    """渲染引导性问题，可选选项"""
    console.print()
    console.print(f"  🤔 [bold]引导问题：[/bold]{question}")
    if options:
        for label, text in options:
            console.print(f"     [{ACCENT}]{label}[/{ACCENT}]  {text}")
    console.print()


def render_flowchart(steps: list, title: str = "执行流程"):
    """用 Rich 渲染 ASCII 流程图（适配视觉化学习）"""
    lines = [f"[{SUB}]▼ {title}[/{SUB}]"]
    for i, step in enumerate(steps):
        connector = "├─" if i < len(steps) - 1 else "└─"
        lines.append(f"  {connector} [bold]Step {i+1}[/bold]: {step}")
    console.print("\n".join(lines))
    console.print()


def render_state_table(states: list, title: str = "状态转移"):
    """渲染算法状态转移表（适配视觉化学习）"""
    if not states:
        return
    headers = list(states[0].keys())
    rows = [[str(v) for v in s.values()] for s in states]
    render_table(headers, rows, title)


def render_error_memory(errors: list):
    """渲染错误记忆档案"""
    if not errors:
        console.print("  [dim]暂无错误记录[/dim]")
        return
    headers = ["时间", "题目类型", "错误类型", "描述"]
    rows = [
        [e["time"], e["category"], e["error_type"], e["description"]]
        for e in errors
    ]
    render_table(headers, rows, "📋 错误记忆档案")


def render_stats(stats: dict):
    """渲染学习统计"""
    console.print()
    layout = Layout()
    layout.split_column(
        Layout(Panel(f"[{SUCCESS}]{stats.get('total_sessions', 0)}", title="学习次数")),
        Layout(Panel(f"[{WARNING}]{stats.get('total_errors', 0)}", title="累计错误")),
        Layout(Panel(f"[{ACCENT}]{stats.get('mastered', 0)}", title="已掌握类别")),
    )
    console.print(layout)


def show_help():
    """显示帮助信息"""
    help_text = """
## 可用命令

| 命令 | 说明 |
|------|------|
| `explain <知识点>` | 可视化讲解某个算法/数据结构 |
| `analyze <代码文件>` | 分析代码的逻辑错误（苏格拉底式引导） |
| `practice <类型>` | 根据错误记忆生成针对性练习题 |
| `memory` | 查看错误记忆档案 |
| `stats` | 查看学习统计 |
| `config` | 配置 API Key / 模型 |
| `help` | 显示此帮助 |
| `quit` | 退出 |

### 示例
```
>>> explain KMP算法的next数组
>>> analyze my_dp_solution.cpp
>>> practice dp
>>> memory
```
"""
    render_markdown(help_text)


def get_multiline_input(prompt: str = "") -> str:
    """获取多行输入（用于粘贴题目描述等），以空行结束"""
    console.print(f"[{ACCENT}]{prompt} (输入空行结束)[/{ACCENT}]")
    lines = []
    first_empty = False
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line == "":
            if first_empty or not lines:
                break
            first_empty = True
            lines.append("")
            continue
        first_empty = False
        lines.append(line)
    return "\n".join(lines)
