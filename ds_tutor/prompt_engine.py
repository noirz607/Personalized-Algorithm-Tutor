"""大模型 Prompt 引擎

三种核心模式:
1. 可视化讲解 — 适配图像化思维
2. 苏格拉底式提问 — 适配理解驱动
3. 代码错误分析 — 引导式 Debug
"""

from openai import OpenAI
from .config import get_api_key, get_api_base, get_model

# ── 系统级指令 ──────────────────────────────

SYSTEM_PROMPT = """你是一个个性化算法学习助手，专门为具有以下学习特点的学生服务：
- 偏图像化思维：喜欢用图、表、流程来理解，不适应大段纯文字
- 理解驱动型：必须搞懂"为什么"，拒绝死记硬背

你的核心原则：
1. 永远不直接给出完整答案或完整代码
2. 用结构化、可视化的方式呈现信息（流程图、状态表、对比表）
3. 用苏格拉底式提问引导学生自主思考
4. 讲解用简体中文，代码和术语保留英文"""

# ── 可视化讲解 Prompt ──────────────────────

EXPLAIN_PROMPT = """## 任务：可视化知识点讲解

请为学生讲解「{topic}」。

### 输出要求

你必须严格按以下结构输出，使用 Markdown 格式：

#### 1. 一句话概览
用一句话说明这个知识点解决什么问题。

#### 2. 可视化流程（使用 Mermaid 图表！）
用 Mermaid 流程图或状态图展示算法执行过程。必须使用以下 Mermaid 格式输出图表：

**流程图示例：**
```mermaid
flowchart TD
  A[开始] --> B[初始化距离数组]
  B --> C{{还有未访问节点?}}
  C -->|是| D[选取距离最小节点]
  D --> E[更新邻居距离]
  E --> C
  C -->|否| F[输出结果]
```

**状态转移示例：**
| Step | 操作 | 状态变化 | 说明 |
|------|------|---------|------|
| 1 | ... | ... | ... |

#### 3. 关键理解点
列出 2-3 个这个知识点最容易出错或最需要理解透彻的地方，用对比表呈现。

#### 4. 引导性问题
提出 2 个苏格拉底式问题（不给答案），引导学生自己思考验证是否真正理解了。

### 格式强制要求（严格遵守！违反会导致渲染失败！）

**表格规则（极其重要）：**
- 表格必须用竖线 | 分隔每一列，格式如下：
  | 列1 | 列2 | 列3 |
  |-----|-----|-----|
  | 值1 | 值2 | 值3 |
- 每行表格前后都要有竖线 |
- 表头和表体之间必须有一行 |---|----|----|
- 绝对禁止用空格或制表符代替竖线 | 来分隔列

**Mermaid 规则（极其重要）：**
- 必须使用三个反引号围栏：```mermaid 开头，``` 结尾
- 节点文本中包含中文或特殊符号时，必须用双引号包裹：A["开始节点"]
- 菱形判断节点使用花括号：C{"条件?"}
- 节点 ID 只能用英文和数字，中文写在引号内

其他规则：
- 不要输出超过 4 行的纯文字段落
- 不要给出完整的解题代码
- 结尾说"请思考上面的问题，可以继续深入探讨"

学生背景：正在学习数据结构与算法，已有 C/C++ 基础。"""

# ── 代码分析 Prompt ────────────────────────

ANALYZE_PROMPT = """## 任务：代码错误分析与 Debug 引导

学生提交了以下代码，请进行引导式错误分析。

### 题目描述
{problem_description}

### 学生代码
```cpp
{code}
```

{memory_context}

### 输出要求

严格按以下结构输出：

#### 1. 逻辑走向分析
用简短流程图描述这段代码实际在做什么（而非学生以为它在做什么）。

#### 2. 疑似问题定位
以表格列出：
| 行号 | 问题类型 | 问题描述 | 严重程度 |
|------|---------|---------|---------|

#### 3. 引导式排错（核心！）
对每个疑似问题，先提出 1 个引导性问题让学自己思考，再给出提示。格式：
- **Q**: <引导性问题>
- **提示**: <如果学生回答不上来，可以给的提示>

**绝对禁止直接给出修改后的正确代码！**

#### 4. 测试建议
给出 1-2 个边界测试用例的建议（不给出完整数据，只描述场景）。

### 重要约束
- 以苏格拉底方式引导，不给答案
- 每次最多给 3 个引导性问题
- 结尾："请先自己尝试修改，修改后输入 'analyze <文件>' 再次提交分析。如果需要更多提示，输入 'hint'。" """

# ── 练习生成 Prompt ────────────────────────

PRACTICE_PROMPT = """## 任务：生成针对性练习题

{memory_context}

### 输出要求

请生成 1 道针对学生薄弱点的练习题：

#### 1. 题目描述
给出题目背景、输入输出格式、数据范围。

#### 2. 为什么选这道题
简要说明这道题针对的是学生的哪个薄弱点。

#### 3. 引导性问题
在给出题目后，附带 1 个引导性提示（不给解法），帮助学生找到突破口。

### 重要约束
- 题目难度适中，不应远超学生当前水平
- 题目应聚焦于学生反复犯错的知识点
- 不要给出解法，只给引导性提示"""

# ── 提示 Prompt (学生要求更多提示时) ──────

HINT_PROMPT = """## 上下文

之前的对话是关于一道算法/数据结构题目的引导式教学。

### 要求
学生刚才请求更多提示。请给出 1 个更进一步的提示（仍然不给答案），这个提示应该：
1. 比之前的引导更具体一点
2. 指向一个具体的思考方向
3. 仍然以问题形式呈现

直接给出提示问题，不需要其他格式。"""


def _get_client() -> OpenAI:
    """获取 OpenAI 客户端"""
    return OpenAI(api_key=get_api_key(), base_url=get_api_base())


def _call_llm(system: str, user: str, stream: bool = False) -> str:
    """调用 LLM，返回响应文本"""
    client = _get_client()
    response = client.chat.completions.create(
        model=get_model(),
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.7,
        stream=stream,
    )
    if stream:
        collected = []
        for chunk in response:
            delta = chunk.choices[0].delta.content
            if delta:
                collected.append(delta)
                print(delta, end="", flush=True)
        print()
        return "".join(collected)
    return response.choices[0].message.content


def explain(topic: str) -> str:
    """可视化讲解某个知识点"""
    return _call_llm(
        SYSTEM_PROMPT,
        EXPLAIN_PROMPT.format(topic=topic),
    )


def analyze_code(code: str, problem_description: str, memory_text: str = "") -> str:
    """分析代码错误，苏格拉底式引导"""
    return _call_llm(
        SYSTEM_PROMPT,
        ANALYZE_PROMPT.format(
            problem_description=problem_description or "（用户未提供题目描述，请仅根据代码逻辑进行分析）",
            code=code,
            memory_context=memory_text,
        ),
    )


def generate_practice(weak_points: str) -> str:
    """生成针对性练习题"""
    memory_context = (
        f"学生的薄弱知识点和高频错误：\n{weak_points}"
        if weak_points
        else "学生暂无历史错误记录，请生成一道中等难度的数据结构与算法综合题。"
    )
    return _call_llm(
        SYSTEM_PROMPT,
        PRACTICE_PROMPT.format(memory_context=memory_context),
    )


def get_hint(context: str = "") -> str:
    """获取更进一步的提示"""
    return _call_llm(
        SYSTEM_PROMPT,
        HINT_PROMPT,
    )
