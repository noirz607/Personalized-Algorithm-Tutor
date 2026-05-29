"""Flask Web 后端 — 个性化算法学习助手可视化界面"""

import json
from flask import Flask, render_template, request, jsonify, Response, stream_with_context

from .prompt_engine import explain, analyze_code, generate_practice
from .memory import (
    record_error,
    get_all_errors,
    check_warnings,
    get_weak_points_summary,
    get_stats,
    mark_mastered,
    get_frequent_patterns,
)
from .config import get_api_key, get_api_base, get_model

app = Flask(__name__, template_folder="templates")

_conversation_history = []
_last_analysis = {"code": "", "category": "", "problem": ""}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/explain", methods=["POST"])
def api_explain():
    data = request.json
    topic = data.get("topic", "")
    if not topic:
        return jsonify({"error": "知识点不能为空"}), 400
    try:
        result = explain(topic)
        return jsonify({"result": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/explain/stream", methods=["POST"])
def api_explain_stream():
    """流式可视化讲解"""
    data = request.json
    topic = data.get("topic", "")
    if not topic:
        return jsonify({"error": "知识点不能为空"}), 400

    def generate():
        try:
            from openai import OpenAI
            from .prompt_engine import SYSTEM_PROMPT, EXPLAIN_PROMPT

            client = OpenAI(api_key=get_api_key(), base_url=get_api_base())
            stream = client.chat.completions.create(
                model=get_model(),
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": EXPLAIN_PROMPT.format(topic=topic)},
                ],
                temperature=0.7,
                stream=True,
            )
            for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield f"data: {json.dumps({'content': delta})}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.route("/api/analyze", methods=["POST"])
def api_analyze():
    data = request.json
    code = data.get("code", "")
    problem = data.get("problem", "")
    if not code:
        return jsonify({"error": "代码不能为空"}), 400

    category = _detect_category(code, problem)
    warnings = check_warnings(category)
    memory_text = get_weak_points_summary() if warnings else ""

    _last_analysis["code"] = code
    _last_analysis["category"] = category
    _last_analysis["problem"] = problem

    try:
        result = analyze_code(code, problem, memory_text)
        return jsonify({"result": result, "warnings": [dict(w) for w in warnings], "category": category})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/analyze/stream", methods=["POST"])
def api_analyze_stream():
    """流式代码分析"""
    data = request.json
    code = data.get("code", "")
    problem = data.get("problem", "")

    def generate():
        try:
            from openai import OpenAI
            from .prompt_engine import SYSTEM_PROMPT, ANALYZE_PROMPT

            category = _detect_category(code, problem)
            warnings = check_warnings(category)
            memory_text = get_weak_points_summary() if warnings else ""
            _last_analysis["code"] = code
            _last_analysis["category"] = category
            _last_analysis["problem"] = problem

            client = OpenAI(api_key=get_api_key(), base_url=get_api_base())
            stream = client.chat.completions.create(
                model=get_model(),
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": ANALYZE_PROMPT.format(
                        problem_description=problem or "（用户未提供题目描述，请仅根据代码逻辑进行分析）",
                        code=code,
                        memory_context=memory_text,
                    )},
                ],
                temperature=0.7,
                stream=True,
            )
            # 先发 warnings
            yield f"data: {json.dumps({'warnings': [dict(w) for w in warnings], 'category': category})}\n\n"
            for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield f"data: {json.dumps({'content': delta})}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.route("/api/hint", methods=["POST"])
def api_hint():
    data = request.json
    context = data.get("context", "")
    try:
        from .prompt_engine import get_hint
        result = get_hint(context)
        return jsonify({"result": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/practice", methods=["POST"])
def api_practice():
    data = request.json
    category = data.get("category", "")
    try:
        weak_points = get_weak_points_summary()
        if category:
            patterns = [p for p in get_frequent_patterns(min_count=1) if p["category"] == category]
            if patterns:
                weak_points = f"重点关注 [{category}] 类型:\n"
                for p in patterns:
                    weak_points += f"- {p['error_type']}: 已出现 {p['cnt']} 次\n"
            else:
                weak_points = f"学生想练习 [{category}] 类型的题目"
        result = generate_practice(weak_points)
        return jsonify({"result": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/memory", methods=["GET"])
def api_memory():
    errors = get_all_errors()
    patterns = get_frequent_patterns(min_count=2)
    return jsonify({
        "errors": [dict(e) for e in errors],
        "patterns": [dict(p) for p in patterns],
    })


@app.route("/api/memory/record", methods=["POST"])
def api_record_error():
    data = request.json
    category = data.get("category", "general")
    error_type = data.get("error_type", "逻辑错误")
    description = data.get("description", "")
    record_error(category, error_type, description)
    return jsonify({"status": "ok"})


@app.route("/api/memory/mark-mastered", methods=["POST"])
def api_mark_mastered():
    data = request.json
    error_type = data.get("error_type", "")
    mark_mastered(error_type)
    return jsonify({"status": "ok"})


@app.route("/api/stats", methods=["GET"])
def api_stats():
    return jsonify(get_stats())


@app.route("/api/config", methods=["GET", "POST"])
def api_config():
    from .config import load_config, save_config

    if request.method == "GET":
        config = load_config()
        return jsonify({
            "has_key": bool(get_api_key()),
            "api_base": config.get("api_base", "https://api.openai.com/v1"),
            "model": config.get("model", "gpt-4o"),
            "masked_key": _mask_key(get_api_key()),
        })
    else:
        data = request.json
        config = load_config()
        if data.get("api_key"):
            config["api_key"] = data["api_key"]
        if data.get("api_base"):
            config["api_base"] = data["api_base"]
        if data.get("model"):
            config["model"] = data["model"]
        save_config(config)
        return jsonify({"status": "ok"})


def _mask_key(key: str) -> str:
    if len(key) <= 8:
        return "****"
    return key[:4] + "****" + key[-4:]


def _detect_category(code: str, problem: str) -> str:
    text = (code + problem).lower()
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


def main():
    """Web 入口"""
    print("\n  🧠 个性化算法学习助手 — Web 界面")
    print("  打开浏览器访问 http://localhost:8080\n")
    app.run(debug=True, port=8080)


if __name__ == "__main__":
    main()
