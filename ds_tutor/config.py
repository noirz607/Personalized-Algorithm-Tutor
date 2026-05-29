"""配置管理"""

import os
import json
from pathlib import Path

CONFIG_DIR = Path.home() / ".ds_tutor"
CONFIG_FILE = CONFIG_DIR / "config.json"
DB_PATH = CONFIG_DIR / "memory.db"


def load_config() -> dict:
    """加载配置，若不存在则返回默认值"""
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    return {}


def save_config(config: dict):
    """保存配置"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")


def get_api_key() -> str:
    """获取 API Key，优先从环境变量读取"""
    return os.environ.get("OPENAI_API_KEY") or load_config().get("api_key", "")


def get_api_base() -> str:
    """获取 API Base URL"""
    return os.environ.get("OPENAI_API_BASE") or load_config().get("api_base", "https://api.deepseek.com")


def get_model() -> str:
    """获取模型名称"""
    return load_config().get("model", "deepseek-chat")
