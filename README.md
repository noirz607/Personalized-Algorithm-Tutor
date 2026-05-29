# 个性化算法学习助手 (Personalized Algorithm Tutor)

> 视觉化讲解 · 苏格拉底式提问 · 错题记忆

## 项目简介

一个基于 CLI 的个性化算法学习助手，专为**偏图像化思维 + 理解驱动型**学习者设计。

核心功能：
- **可视化知识点讲解**：用状态表、流程图呈现算法执行过程，告别大段文字
- **苏格拉底式提问**：不直接给答案，用层层递进的提问引导自主思考
- **代码错误分析**：提交代码后分析逻辑走向，定位问题行号并给出引导性问题
- **个人错题记忆库**：记录高频错误模式，下次遇到同类问题时主动预警

## 安装

```bash
# 克隆仓库
git clone <repo-url>
cd 人工智能的数学思维

# 安装依赖
pip install -r requirements.txt
```

## 配置

```bash
# 方式一：环境变量
export OPENAI_API_KEY="your-api-key"
export OPENAI_API_BASE="https://api.openai.com/v1"  # 可选，默认 OpenAI

# 方式二：启动后在程序内运行 config 命令配置
```

## 使用

```bash
python -m ds_tutor.main
```

启动后支持的命令：

| 命令 | 说明 |
|------|------|
| `explain <知识点>` | 可视化讲解某个算法/数据结构 |
| `analyze <代码文件>` | 分析代码逻辑错误（苏格拉底式引导） |
| `hint` | 对上一次分析请求更多提示 |
| `practice <类型>` | 根据错误记忆生成针对性练习题 |
| `memory` | 查看错误记忆档案 |
| `stats` | 查看学习统计 |
| `config` | 配置 API Key / 模型 |
| `help` | 显示帮助 |
| `quit` | 退出 |

## 项目结构

```
ds_tutor/
├── __init__.py     # 包元信息
├── main.py         # CLI 入口
├── cli.py          # Rich 终端界面
├── prompt_engine.py # LLM Prompt 引擎
├── tutor.py        # 核心调度逻辑
├── memory.py       # SQLite 错误记忆库
└── config.py       # 配置管理
```

## 技术栈

- **Python 3.9+**
- **OpenAI API** (兼容任何 OpenAI 格式的 API)
- **Rich** — 终端 UI 渲染
- **SQLite** — 本地错误记忆存储
