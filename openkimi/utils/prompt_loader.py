import os
from typing import Dict

_prompt_cache: Dict[str, str] = {}
PROMPT_DIR = os.path.join(os.path.dirname(__file__), '..', 'prompts')

def load_prompt(name: str) -> str:
    """
    从 prompts/ 目录加载指定名称的提示模板。

    Args:
        name: 提示文件的名称（不含扩展名）。

    Returns:
        提示模板字符串。

    Raises:
        FileNotFoundError: 如果找不到对应的 .prompt 文件。
    """
    if name in _prompt_cache:
        return _prompt_cache[name]

    file_path = os.path.join(PROMPT_DIR, f"{name}.prompt")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Prompt file not found: {file_path}")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            prompt_template = f.read()
            _prompt_cache[name] = prompt_template
            return prompt_template
    except Exception as e:
        raise IOError(f"Error reading prompt file {file_path}: {e}") from e 