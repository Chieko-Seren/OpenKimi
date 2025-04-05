<div align="center">

<h1> OpenKimi ✨ </h1>

_让LLM突破上下文长度限制的宇宙飞船_

[![License](https://img.shields.io/badge/License-MIT%20License-blue.svg)](https://opensource.org/licenses/MIT%20License)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Stars](https://img.shields.io/github/stars/Chieko-Seren/openkimi.svg?style=social&label=Star)](https://github.com/yourusername/openkimi)
[![Issues](https://img.shields.io/github/issues/Chieko-Seren/openkimi.svg)](https://github.com/yourusername/openkimi/issues)


  <img src="https://i.postimg.cc/6qdQbvPf/open-kimi.png">
</div>

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

### 文本处理和信息熵计算
OpenKimi 使用信息熵来评估文本块的信息密度，这使得系统能够智能地识别哪些内容值得保留在主上下文中，哪些可以暂时存储到 RAG 中。

```python
from openkimi.core import TextProcessor

processor = TextProcessor(batch_size=512)
batches = processor.split_into_batches(long_text)
useful, less_useful = processor.classify_by_entropy(batches)
```

### RAG 管理
非关键文本会被摘要并存储到 RAG 系统中，需要时可以动态检索回来：

```python
from openkimi.core import RAGManager
from openkimi.utils.llm_interface import get_llm_interface

llm = get_llm_interface({"type": "dummy"})
rag = RAGManager(llm)
summaries = rag.batch_store(less_useful_texts)
relevant_texts = rag.retrieve("相关查询")
```

### 框架生成
将复杂问题分解为步骤，确保解决方案的质量：

```python
from openkimi.core import FrameworkGenerator

framework_gen = FrameworkGenerator(llm)
solution_framework = framework_gen.generate_framework("复杂问题")
solution = framework_gen.generate_solution("复杂问题", solution_framework)
```

## 🚀 使用案例

### 1. 处理超长文档

```python
from openkimi import KimiEngine

engine = KimiEngine()
with open("book.txt", "r") as f:
    engine.ingest(f.read())

# 可以处理远超传统LLM上下文窗口的文档
response = engine.chat("分析这本书的主题和写作风格")
print(response)
```

### 2. 统一处理不同LLM

```python
# 使用本地模型
engine1 = KimiEngine(llm="./models/my_model")

# 使用API
import os
os.environ["LLM_API_KEY"] = "your-api-key"
engine2 = KimiEngine(config_path="config_api.json")
```

## ⚙️ 配置选项

OpenKimi 支持丰富的配置选项，主要包括：

1. **LLM 设置**：选择模型类型，设置路径或API密钥
2. **处理器设置**：调整批次大小和信息熵阈值
3. **RAG 设置**：控制摘要和检索行为
4. **框架设置**：定制问题解决框架的生成方式

示例配置文件:
```json
{
    "llm": {
        "type": "api",
        "api_key": "your-api-key",
        "api_url": "https://api.example.com/v1/completions"
    },
    "processor": {
        "batch_size": 1024,
        "entropy_threshold": 2.5
    }
}
```

## 🌈 未来计划

- [ ] 添加更多 LLM 后端支持
- [ ] 实现向量数据库集成，提升 RAG 性能
- [ ] 添加更细粒度的信息熵评估方式
- [ ] 支持多模态输入
- [ ] 增强跨文档推理能力
