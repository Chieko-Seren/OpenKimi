<div align="center">

<h1> OpenKimi ✨ </h1>

_让LLM突破上下文长度限制的宇宙飞船_

[![License](https://img.shields.io/badge/License-MIT%20License-blue.svg)](https://opensource.org/licenses/MIT%20License)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Stars](https://img.shields.io/github/stars/Chieko-Seren/openkimi.svg?style=social&label=Star)](https://github.com/yourusername/openkimi)
[![Issues](https://img.shields.io/github/issues/Chieko-Seren/openkimi.svg)](https://github.com/yourusername/openkimi/issues)


  <img src="https://i.postimg.cc/6qdQbvPf/open-kimi.png">
</div>

[在线 Demo](https://chieko-seren.github.io/OpenKimi/) | [QQ 群组](https://qm.qq.com/q/65zMQ7fMrY) | [查看开发文档](https://github.com/Chieko-Seren/OpenKimi/blob/main/docs/index.md) | [报告安全漏洞](https://github.com/Chieko-Seren/OpenKimi/security)

## 🌟 项目介绍
OpenKimi 是首个面向开发者的**无限上下文LLM支持框架**，旨在打破传统大语言模型（LLM）的上下文长度限制。通过革命性的上下文管理算法和高效的内存优化技术，OpenKimi 为开发者提供了一个强大的工具，让模型能够处理超大规模文本数据并进行深度语义推理。我们实现了：

- ✅ **百万级Token支持**：轻松处理超长文本，无论是小说、论文还是代码库。
- ✅ **零精度损失的内存压缩**：在保持模型推理质量的同时大幅降低内存占用。
- ✅ **跨模型的统一接口**：支持主流LLM（如 LLaMA、GPT 等），无需为不同模型调整代码。
- ✅ **实时动态上下文优化**：根据输入动态调整上下文窗口，确保性能与效率的完美平衡。

OpenKimi 的目标是突破传统 LLM 的"上下文监狱"，让模型能够真正理解完整的人类知识体系，从单一对话到整个知识图谱，助力开发者构建更智能、更具洞察力的应用。

## 🌍 为什么选择 OpenKimi？
- **无限可能**：无论是分析整部《战争与和平》、理解复杂的技术文档，还是推理跨领域的知识，OpenKimi 都能胜任。
- **开发者友好**：简洁的 API 设计，几行代码即可上手。
- **开源精神**：完全开源，社区驱动，欢迎每一位探索者的贡献。

## 🚀 快速体验

### 安装
确保你有 Python 3.8+ 环境，然后运行以下命令安装 OpenKimi：

```bash
pip install openkimi
```

### 示例代码
以下是一个简单的例子，展示如何使用 OpenKimi 加载《三体》全文并进行深度分析：

```python
from openkimi import KimiEngine

# 初始化任意大语言模型（替换为你的模型路径）
engine = KimiEngine(llm="your-model-path")

# 加载《三体》全文本（约30万字）
with open("three_body.txt", "r", encoding="utf-8") as f:
    engine.ingest(f.read())

# 进行深度语义推理
response = engine.chat("请分析第二部《黑暗森林》的核心隐喻")
print(response)
```


## 🛠️ 系统要求
- **操作系统**：Windows、Linux 或 macOS
- **Python 版本**：3.8 或更高
- **内存**：建议 16GB+（根据模型和输入规模而定）
- **依赖**：详见 `requirements.txt`

## 📖 使用指南
1. **安装依赖**：
   ```bash
   pip install -r requirements.txt
   ```
2. **配置模型**：将你的 LLM 模型路径传入 `KimiEngine`。
3. **加载数据**：使用 `ingest()` 方法加载任意长度的文本。
4. **开始推理**：调用 `chat()` 或其他接口获取结果。

## 🌠 应用场景
- **文学分析**：理解长篇小说的情节、主题和隐喻。
- **技术文档处理**：快速提取代码库或论文的关键信息。
- **知识管理**：构建个人知识库，回答跨文档的问题。
- **教育与研究**：辅助学术研究，处理超大规模数据集。

## 🤝 参与贡献
OpenKimi 是社区驱动的开源项目，我们拥抱星辰大海，期待您的加入！以下是参与方式：

1. **提交 Issue**：讨论新功能、报告 Bug 或提出优化建议。
2. **Fork 仓库**：克隆项目到本地进行开发。
3. **提交 Pull Request**：开发完成后关联相关 Issue，提交代码。
4. **代码审查**：通过 CI 测试后，等待 maintainers 审核合并。

## 🌟 致谢
感谢所有为 OpenKimi 做出贡献的开发者、测试者和用户！

## 📬 联系我们
- **GitHub Issues**： https://github.com/Chieko-Seren/OpenKimi/issues
- **邮箱**：chieko.seren@icloud.com

## 🔍 项目结构

```
openkimi/
├── core/              # 核心功能实现
│   ├── engine.py      # 主引擎
│   ├── processor.py   # 文本处理器
│   ├── rag.py         # RAG管理
│   └── framework.py   # 框架生成
├── utils/             # 工具类
│   └── llm_interface.py # LLM接口
└── __init__.py        # 包初始化
```

## 🧠 核心功能详解

OpenKimi 通过以下核心机制实现无限上下文处理：

### 文本处理和信息熵计算
- **分块**: 将长文本切分为可管理的大小 (`batch_size`)。
- **信息熵评估**: 使用词频计算每个块的信息熵，评估其信息密度。
- **分类**: 低于阈值 (`entropy_threshold`) 的块被视为信息密度较低。

```python
from openkimi.core import TextProcessor

processor = TextProcessor(batch_size=512)
batches = processor.split_into_batches(long_text)
useful, less_useful = processor.classify_by_entropy(batches, threshold=3.0)
```

### RAG 管理 (向量检索)
- **存储**: 低信息熵文本块通过 LLM 进行摘要，摘要和原文一同存储。摘要文本被转换为向量（使用 `sentence-transformers`）并索引。
- **检索**: 当需要额外上下文时，用户查询被转换为向量，通过计算与存储的摘要向量之间的余弦相似度来检索最相关的原文块 (`top_k`)。
- **高效向量检索**: 使用FAISS（Facebook AI相似性搜索）进行高效向量索引和检索，显著提升大规模向量集合的检索速度。

```python
from openkimi.core import RAGManager
from openkimi.utils.llm_interface import get_llm_interface

llm = get_llm_interface({"type": "dummy"})
# 启用FAISS加速向量检索
rag = RAGManager(llm, embedding_model_name='all-MiniLM-L6-v2', use_faiss=True) 
summaries = rag.batch_store(less_useful_texts)
relevant_texts = rag.retrieve("相关查询", top_k=3)
```

### 递归 RAG 压缩
- **上下文超限处理**: 在调用 LLM（用于摘要、框架生成、解决方案生成等）之前，如果构造的 Prompt 超过模型的最大上下文长度 (`max_prompt_tokens`)，OpenKimi 会自动触发递归 RAG 压缩。
- **压缩过程**: 超长的文本会被分块、计算信息熵，低信息熵部分被临时 RAG 存储（生成摘要并向量化），只保留高信息熵部分和低信息熵部分的摘要，形成压缩后的文本。此过程可递归进行，直至文本长度符合要求。

### 框架生成 & MCP
- **框架生成**: 将复杂问题分解为步骤，确保解决方案的逻辑性。
- **MCP (Mixture of Context Prompters)**: （可选，通过 `mcp_candidates` 配置）为同一个问题生成多个候选解决方案（可能基于上下文的不同侧重或随机性），然后通过最终的 LLM 调用将这些候选方案综合成一个更全面、更鲁棒的最终答案。

```python
from openkimi.core import FrameworkGenerator

framework_gen = FrameworkGenerator(llm)
solution_framework = framework_gen.generate_framework("复杂问题", context=relevant_history)
# 使用 MCP (假设 mcp_candidates > 1)
final_solution = framework_gen.generate_solution_mcp(
    "复杂问题", 
    solution_framework, 
    useful_context=relevant_history, 
    rag_context=retrieved_rag_texts, 
    num_candidates=3
)
```

### 可插拔 LLM 接口
- 支持 `dummy` (用于测试), `local` (使用 Hugging Face `transformers` 加载本地模型) 和 `api` (兼容 OpenAI Chat Completion API) 类型。
- 通过配置文件或初始化参数轻松切换。

## ⚙️ 配置选项

通过 JSON 配置文件 (`config.json`) 或 `KimiEngine` 初始化参数进行配置：

- **`llm`**: 
    - `type`: "dummy", "local", "api"
    - `model_path`: (local) 模型路径或 HF Hub 名称
    - `device`: (local) "auto", "cpu", "cuda", "mps"
    - `api_key`: (api) API 密钥 (或从 `OPENAI_API_KEY` 环境变量读取)
    - `api_url`: (api) API 端点 (或从 `OPENAI_API_BASE` 环境变量读取)
    - `model_name`: (api) 使用的模型名称 (e.g., "gpt-4")
    - `context_length`: (api/local) 模型上下文长度 (Token 数)
- **`processor`**: 
    - `batch_size`: 文本分块大小
    - `entropy_threshold`: 低于此熵值的块进入 RAG
- **`rag`**: 
    - `embedding_model`: Sentence Transformer 模型名称 (e.g., "all-MiniLM-L6-v2")
    - `top_k`: 检索时返回的相关文本块数量
- **`mcp_candidates`**: MCP 候选方案数量 (1 表示禁用)

示例 (`config.json`):
```json
{
    "llm": {
        "type": "local",
        "model_path": "gpt2", // Or your local model path
        "device": "auto",
        "context_length": 1024
    },
    "processor": {
        "batch_size": 256,
        "entropy_threshold": 2.8
    },
    "rag": {
        "embedding_model": "all-MiniLM-L6-v2",
        "top_k": 5
    },
    "mcp_candidates": 3 // Enable MCP with 3 candidates
}
```

## 🌐 OpenAI 兼容 API 服务器

OpenKimi 提供了一个 FastAPI 服务器，用于暴露 OpenAI Chat Completion 兼容的 API 端点。

**启动服务器:**

```bash
# Make sure dependencies are installed: pip install -r requirements.txt

# Set API Key if using API backend for the engine itself
# export OPENAI_API_KEY="sk-..."

python -m openkimi.api.server --config examples/config.json --port 8000 --host 0.0.0.0
```

**可用参数:**
- `--host`: 监听地址 (默认: 127.0.0.1)
- `--port`: 监听端口 (默认: 8000)
- `--config` / `-c`: KimiEngine 配置文件路径
- `--mcp-candidates`: 覆盖配置中的 MCP 候选数量
- `--reload`: 开发模式，代码更改时自动重载

**API 端点:**
- `POST /v1/chat/completions`: 处理聊天请求。
- `GET /health`: 检查服务器和引擎状态。

**使用示例 (curl):**

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

> [!WARNING]
> 本项目不是 Starlight Dream 的维护项目，与 Starlight Dream 无任何关系，并且不保障稳定的维护。
