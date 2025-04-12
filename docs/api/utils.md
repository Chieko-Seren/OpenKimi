# 工具 API 参考

本页详细介绍 `openkimi.utils` 模块中的类和函数。

## LLMInterface

所有LLM实现的抽象基类。

```python
from abc import ABC, abstractmethod
from typing import Any, Optional

class LLMInterface(ABC):
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        pass
        
    @abstractmethod
    def stream_generate(self, prompt: str, **kwargs) -> Generator[str, None, None]:
        pass
        
    @abstractmethod
    def get_tokenizer(self) -> Any:
        pass
        
    @abstractmethod
    def get_max_context_length(self) -> int:
        pass
```

- `generate`: 生成文本回复。
- `stream_generate`: 流式生成文本回复。
- `get_tokenizer`: 获取模型使用的tokenizer。
- `get_max_context_length`: 获取模型的最大上下文长度。

## Model Factory (`get_llm_interface`)

根据配置创建LLM接口实例的工厂函数。

```python
from typing import Dict, Any

def get_llm_interface(llm_config: Dict[str, Any]) -> Optional[LLMInterface]:
    pass
```

- **参数**：
    - `llm_config` (Dict): LLM配置字典，结构见[配置指南](../guides/configuration.md)。
- **返回**：
    - 相应的`LLMInterface`实例或`None`（如果配置无效）。

## TokenCounter

用于计算文本token数量的工具类。

```python
class TokenCounter:
    def __init__(self, tokenizer: Any):
        pass
        
    def count_tokens(self, text: str) -> int:
        pass
```

- `__init__`: 初始化计数器，需要传入一个tokenizer实例。
- `count_tokens`: 计算给定文本的token数量。

## PromptLoader (`load_prompt`)

从文件加载提示模板的函数。

```python
from typing import Dict

def load_prompt(name: str) -> str:
    pass
```

- **参数**：
    - `name` (str): 提示文件的名称（不含扩展名），文件应位于`openkimi/prompts/`目录下。
- **返回**：
    - 提示模板字符串。
- **异常**：
    - `FileNotFoundError`: 如果找不到对应的`.prompt`文件。
    - `IOError`: 如果读取文件时出错。 