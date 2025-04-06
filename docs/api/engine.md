# KimiEngine

`KimiEngine` 是 OpenKimi 的核心类，负责整合所有功能模块，提供无限上下文长度的大语言模型对话能力。

## 初始化

```python
from openkimi import KimiEngine

engine = KimiEngine(
    config_path=None,         # 配置文件路径
    llm_config=None,          # LLM 配置字典
    processor_config=None,    # 文本处理器配置字典
    rag_config=None,          # RAG 配置字典
    mcp_candidates=1          # MCP 候选方案数量（1表示禁用MCP）
)
```

### 参数

- **config_path** (`str`, 可选): 配置文件的路径（JSON格式）
- **llm_config** (`dict`, 可选): LLM 配置字典，会覆盖配置文件中的设置
- **processor_config** (`dict`, 可选): 文本处理器配置字典，会覆盖配置文件中的设置
- **rag_config** (`dict`, 可选): RAG 配置字典，会覆盖配置文件中的设置
- **mcp_candidates** (`int`, 可选): MCP 候选方案数量，默认为 1（表示禁用 MCP）

### 配置格式

配置文件为 JSON 格式，基本结构如下：

```json
{
    "llm": {
        "type": "api",                          // "dummy", "local", "api"
        "api_key": "your-api-key",              // 用于 API 类型
        "api_url": "https://api.openai.com",    // 用于 API 类型
        "model_name": "gpt-4",                  // 用于 API 类型
        "model_path": "gpt2",                   // 用于 local 类型
        "device": "auto",                       // 用于 local 类型
        "context_length": 8192                  // 模型上下文长度
    },
    "processor": {
        "batch_size": 512,                      // 文本分块大小
        "entropy_threshold": 3.0                // 信息熵阈值
    },
    "rag": {
        "embedding_model": "all-MiniLM-L6-v2",  // 嵌入模型名称
        "top_k": 3                              // 检索返回的文本块数量
    },
    "mcp_candidates": 1                         // MCP 候选方案数量
}
```

## 方法

### ingest

摄入文本，进行预处理和 RAG 存储。

```python
engine.ingest(text)
```

**参数:**
- **text** (`str`): 要摄入的文本内容

**返回:** `None`

**示例:**
```python
with open("document.txt", "r", encoding="utf-8") as f:
    engine.ingest(f.read())
```

### chat

处理用户查询并生成回复。

```python
response = engine.chat(query)
```

**参数:**
- **query** (`str`): 用户查询文本

**返回:** `str` - 模型生成的回复

**示例:**
```python
response = engine.chat("文档的主要内容是什么？")
print(response)
```

### reset

重置会话历史和 RAG 存储。

```python
engine.reset()
```

**参数:** 无

**返回:** `None`

**示例:**
```python
# 重置会话，开始一个新的对话
engine.reset()
```

## 内部方法

以下是一些内部方法，通常不需要直接调用：

### _load_config

从 JSON 文件加载配置，合并默认值。

### _recursive_rag_compress

递归地使用 RAG 压缩文本，直到符合 token 限制。

### _prepare_llm_input

确保 prompt 符合模型的上下文长度限制。

### _get_recent_context

获取最近的对话历史，确保其符合 token 限制。 