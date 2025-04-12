# 配置选项

OpenKimi提供了灵活的配置选项，可以通过JSON配置文件或初始化参数进行设置。本文档详细介绍所有可用的配置选项。

## 配置方式

可以通过以下两种方式配置OpenKimi：

1. **JSON配置文件**：将所有配置存储在一个JSON文件中
2. **初始化参数**：在创建`KimiEngine`实例时直接传入配置参数

示例：

```python
# 使用配置文件
engine = KimiEngine(config_path="config.json")

# 使用初始化参数
engine = KimiEngine(
    llm_config={"type": "local", "model_path": "gpt2"},
    processor_config={"batch_size": 256},
    rag_config={"top_k": 5},
    mpr_candidates=3
)
```

## 配置文件结构

完整的配置文件结构如下：

```json
{
    "llm": {
        "type": "api",
        "api_key": "your-api-key",
        "api_url": "https://api.openai.com/v1",
        "model_name": "gpt-3.5-turbo",
        "device": "auto",
        "model_path": "",
        "context_length": 4096,
        "load_in_8bit": false,
        "load_in_4bit": false
    },
    "processor": {
        "batch_size": 512,
        "entropy_threshold": 2.8,
        "overlap_size": 50,
        "entropy_method": "weighted"
    },
    "rag": {
        "embedding_model": "all-MiniLM-L6-v2",
        "top_k": 5,
        "use_faiss": true,
        "similarity_threshold": 0.7
    },
    "mpr_candidates": 3
}
```

## LLM配置选项

`llm`部分控制语言模型的配置：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `type` | string | `"dummy"` | 模型类型，可选值：`"dummy"`、`"local"`、`"api"` |
| `api_key` | string | 环境变量 | API密钥（用于`type="api"`）。默认从`OPENAI_API_KEY`环境变量读取 |
| `api_url` | string | 环境变量 | API端点（用于`type="api"`）。默认从`OPENAI_API_BASE`环境变量读取 |
| `model_name` | string | `"gpt-3.5-turbo"` | 模型名称，用于API类型或本地模型的HF Hub ID |
| `device` | string | `"auto"` | 设备选择（用于`type="local"`），可选值：`"auto"`、`"cpu"`、`"cuda"`、`"mps"` |
| `model_path` | string | `""` | 本地模型路径或HF Hub ID（用于`type="local"`） |
| `context_length` | integer | 模型默认值 | 模型的最大上下文长度 |
| `load_in_8bit` | boolean | `false` | 是否以8位精度加载模型（用于`type="local"`） |
| `load_in_4bit` | boolean | `false` | 是否以4位精度加载模型（用于`type="local"`） |

## 处理器配置选项

`processor`部分控制文本处理器的行为：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `batch_size` | integer | `512` | 文本分块大小（以词为单位） |
| `entropy_threshold` | float | `2.5` | 信息熵阈值，低于此值的块被认为信息密度低 |
| `overlap_size` | integer | `50` | 文本块之间的重叠大小（以词为单位） |
| `entropy_method` | string | `"weighted"` | 信息熵计算方法，可选值：`"word"`、`"ngram"`、`"semantic"`、`"structural"`、`"weighted"` |

## RAG配置选项

`rag`部分控制RAG管理器的行为：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `embedding_model` | string | `"all-MiniLM-L6-v2"` | 用于生成嵌入的模型名称 |
| `top_k` | integer | `3` | 检索时返回的相关文本块数量 |
| `use_faiss` | boolean | `true` | 是否使用FAISS进行向量检索 |
| `similarity_threshold` | float | `0.7` | 相似度阈值，低于此值的结果将被过滤 |

## MPR配置选项

MPR（Multi Path Reasoning）相关配置：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `mpr_candidates` | integer | `1` | MPR候选方案数量，设为1表示禁用MPR |

## 环境变量

OpenKimi也支持通过环境变量进行一些基本配置：

- `OPENAI_API_KEY`: OpenAI API密钥
- `OPENAI_API_BASE`: OpenAI API端点
- `OPENKIMI_CONFIG_PATH`: 默认配置文件路径

## 示例配置

### 使用OpenAI API

```json
{
    "llm": {
        "type": "api",
        "api_key": "sk-...",
        "model_name": "gpt-4"
    },
    "processor": {
        "batch_size": 512,
        "entropy_threshold": 2.8
    },
    "rag": {
        "top_k": 5
    },
    "mpr_candidates": 3
}
```

### 使用本地模型

```json
{
    "llm": {
        "type": "local",
        "model_path": "meta-llama/Llama-2-7b-chat-hf",
        "device": "cuda",
        "load_in_8bit": true
    },
    "processor": {
        "batch_size": 256,
        "entropy_threshold": 2.5
    },
    "rag": {
        "embedding_model": "all-MiniLM-L6-v2",
        "top_k": 3
    },
    "mpr_candidates": 2
}
```

## 程序化配置

你也可以在代码中动态生成和修改配置：

```python
import json
from openkimi import KimiEngine

# 创建配置字典
config = {
    "llm": {
        "type": "api",
        "api_key": "your-api-key",
        "model_name": "gpt-3.5-turbo"
    },
    "processor": {
        "batch_size": 512,
        "entropy_method": "semantic"
    },
    "rag": {
        "embedding_model": "all-MiniLM-L6-v2",
        "top_k": 5,
        "use_faiss": True
    },
    "mpr_candidates": 3
}

# 保存配置到文件
with open("my_config.json", "w", encoding="utf-8") as f:
    json.dump(config, f, indent=4)

# 使用配置文件初始化引擎
engine = KimiEngine(config_path="my_config.json")

# 或者直接使用配置字典
engine = KimiEngine(
    llm_config=config["llm"],
    processor_config=config["processor"],
    rag_config=config["rag"],
    mpr_candidates=config["mpr_candidates"]
)
```

## 参数优先级

当多种配置方式同时存在时，参数的优先级从高到低为：

1. 初始化参数（`llm_config`、`processor_config`等）
2. 配置文件（`config_path`）
3. 默认值 