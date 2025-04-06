# 快速开始

本指南将帮助你安装 OpenKimi 并运行你的第一个无限上下文 LLM 应用。

## 安装

确保你有 Python 3.8+ 环境，然后运行以下命令安装 OpenKimi：

```bash
pip install openkimi
```

或者，你可以从源代码安装（推荐用于开发）：

```bash
git clone https://github.com/Chieko-Seren/OpenKimi.git
cd OpenKimi
pip install -r requirements.txt
```

## 基本使用

以下是一个简单的例子，展示如何使用 OpenKimi 加载长文本并进行对话：

```python
from openkimi import KimiEngine

# 初始化 KimiEngine（使用默认配置）
engine = KimiEngine()

# 加载长文本（例如一本书、论文或文档）
with open("long_document.txt", "r", encoding="utf-8") as f:
    engine.ingest(f.read())

# 进行对话
response = engine.chat("请总结这个文档的主要内容")
print(response)

# 继续对话
response = engine.chat("这个文档讨论了哪些关键概念？")
print(response)

# 重置对话历史
engine.reset()
```

## 配置 LLM 后端

OpenKimi 支持多种 LLM 后端，可以通过配置文件或初始化参数进行设置：

### 使用配置文件

创建 `config.json`：

```json
{
    "llm": {
        "type": "api",
        "api_key": "你的API密钥",
        "model_name": "gpt-4",
        "context_length": 8192
    },
    "processor": {
        "batch_size": 512,
        "entropy_threshold": 3.0
    },
    "rag": {
        "embedding_model": "all-MiniLM-L6-v2",
        "top_k": 5
    },
    "mcp_candidates": 3
}
```

然后使用配置文件初始化：

```python
engine = KimiEngine(config_path="config.json")
```

### 直接传递参数

```python
engine = KimiEngine(
    llm_config={
        "type": "local",
        "model_path": "meta-llama/Llama-2-7b-chat-hf",
        "device": "cuda",
        "context_length": 4096
    },
    processor_config={
        "batch_size": 256
    },
    mcp_candidates=1  # 禁用 MCP
)
```

## 启动 API 服务器

OpenKimi 提供了一个与 OpenAI 兼容的 API 服务器：

```bash
# 启动服务器
python run_server.py --config config.json --host 0.0.0.0 --port 8000

# 或者使用模块
python -m openkimi.api.server --config config.json
```

然后你可以使用标准的 API 调用与服务器交互：

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openkimi-model", 
    "messages": [
      {"role": "system", "content": "这是需要处理的长文档内容..."},
      {"role": "user", "content": "请根据文档回答这个问题？"}
    ]
  }'
```

## 下一步

- 阅读[核心概念](./concepts.md)了解 OpenKimi 的工作原理
- 查看[API 参考](../api/index.md)获取详细的 API 文档
- 浏览[示例](../examples/index.md)了解更多应用场景 