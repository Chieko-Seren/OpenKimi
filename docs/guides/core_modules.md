# 核心模块

OpenKimi由几个核心模块组成，每个模块负责系统的不同方面。本文档详细介绍每个核心模块的功能和用法。

## KimiEngine

`KimiEngine`是整个系统的主引擎，负责协调各个模块的工作，提供统一的对话接口。

### 主要功能

- 初始化和配置系统组件
- 处理用户查询并生成回复
- 管理会话历史
- 协调RAG、文本处理和框架生成

### 主要方法

| 方法 | 描述 |
|------|------|
| `__init__(config_path, llm_config, processor_config, rag_config, mpr_candidates, session_id)` | 初始化引擎 |
| `ingest(text)` | 摄入和处理长文本 |
| `chat(query)` | 处理用户查询并生成回复 |
| `stream_chat(query)` | 流式处理用户查询并生成回复 |
| `reset()` | 重置会话历史和RAG存储 |

### 使用示例

```python
from openkimi import KimiEngine

# 初始化引擎
engine = KimiEngine()

# 加载长文本
engine.ingest("这是一个很长的文本...")

# 提问
response = engine.chat("请总结这篇文章的主要内容")
print(response)

# 重置会话
engine.reset()
```

## TextProcessor

`TextProcessor`负责文本分割、信息熵计算和文本块评估，是处理长文本的关键组件。

### 主要功能

- 将长文本分割成可管理的块
- 计算文本块的信息熵
- 根据信息熵对文本块进行分类
- 提取关键信息片段

### 主要方法

| 方法 | 描述 |
|------|------|
| `__init__(batch_size, entropy_threshold, overlap_size, entropy_method)` | 初始化处理器 |
| `split_into_batches(text, by_sentence)` | 将文本分割成批次 |
| `calculate_entropy(text, context_texts)` | 计算文本的信息熵 |
| `classify_by_entropy(batches, threshold, context_aware)` | 根据信息熵对文本块进行分类 |
| `get_batch_entropy_ranking(batches, context_aware)` | 获取文本块的熵值排名 |
| `extract_key_segments(text, top_k)` | 提取文本中信息熵最高的片段 |

### 使用示例

```python
from openkimi.core import TextProcessor

# 初始化处理器
processor = TextProcessor(batch_size=512, entropy_threshold=2.5)

# 分割文本
text = "这是一个很长的文本..."
batches = processor.split_into_batches(text)

# 根据信息熵分类
useful_batches, less_useful_batches = processor.classify_by_entropy(batches)

# 提取关键片段
key_segments = processor.extract_key_segments(text, top_k=3)
```

## RAGManager

`RAGManager`管理向量存储和检索系统，处理低信息密度的文本块。

### 主要功能

- 使用文本摘要和向量存储实现高效检索
- 支持类似文本的高效检索
- 处理递归RAG压缩
- 管理向量索引和存储

### 主要方法

| 方法 | 描述 |
|------|------|
| `__init__(model, embedding_model_name, use_faiss, max_chunk_size, overlap_size, similarity_threshold)` | 初始化RAG管理器 |
| `add_text(text)` | 添加文本到RAG存储 |
| `search(query, top_k)` | 搜索相关文本 |
| `_recursive_rag_compress(text)` | 递归RAG压缩 |
| `batch_store(texts)` | 批量存储文本 |
| `retrieve(query, top_k)` | 检索与查询最相关的文本 |

### 使用示例

```python
from openkimi.core import RAGManager
from openkimi.core.models import OpenAIModel

# 初始化模型
model = OpenAIModel(api_key="your-api-key")

# 初始化RAG管理器
rag = RAGManager(model, embedding_model_name="all-MiniLM-L6-v2", use_faiss=True)

# 添加文本
rag.add_text("这是一个需要存储的文本...")

# 检索相关内容
results = rag.search("查询关键词", top_k=3)
```

## FrameworkGenerator

`FrameworkGenerator`负责生成解决方案框架和最终答案，实现多路径推理（MPR）策略。

### 主要功能

- 将复杂问题分解为逻辑步骤
- 支持多种上下文采样策略
- 支持多种解决方案合成策略
- 生成全面的最终解决方案

### 主要方法

| 方法 | 描述 |
|------|------|
| `__init__(model)` | 初始化框架生成器 |
| `generate_framework(query, context)` | 生成解决方案框架 |
| `generate_solution_mpr(query, framework, useful_context, rag_context, num_candidates, context_strategy, synthesis_strategy)` | 使用MPR策略生成解决方案 |

### 使用示例

```python
from openkimi.core import FrameworkGenerator
from openkimi.core.models import OpenAIModel

# 初始化模型
model = OpenAIModel(api_key="your-api-key")

# 初始化框架生成器
framework_gen = FrameworkGenerator(model)

# 生成框架
framework = framework_gen.generate_framework("如何提高学习效率？", "上下文内容...")

# 生成解决方案（使用MPR）
solution = framework_gen.generate_solution_mpr(
    "如何提高学习效率？",
    framework,
    useful_context="上下文内容...",
    rag_context=["相关文本1", "相关文本2"],
    num_candidates=3,
    context_strategy="diversity",
    synthesis_strategy="hierarchical"
)
```

## EntropyEvaluator

`EntropyEvaluator`提供多种信息熵计算方法，用于评估文本块的信息密度。

### 主要功能

- 词级别信息熵计算
- N-gram级别信息熵计算
- 语义级别信息熵计算
- 结构级别信息熵计算
- 综合评估文本的信息熵

### 主要方法

| 方法 | 描述 |
|------|------|
| `__init__(use_tfidf, ngram_range, max_features)` | 初始化熵评估器 |
| `calculate_word_entropy(text)` | 计算词级别的信息熵 |
| `calculate_ngram_entropy(text, n)` | 计算n-gram级别的信息熵 |
| `calculate_semantic_entropy(texts)` | 计算语义级别的信息熵 |
| `calculate_structural_entropy(text)` | 计算结构级别的信息熵 |
| `evaluate_text(text, texts, weights)` | 综合评估文本的信息熵 |

### 使用示例

```python
from openkimi.core import EntropyEvaluator

# 初始化熵评估器
evaluator = EntropyEvaluator()

# 计算文本的信息熵
text = "这是一个示例文本..."
entropy_results = evaluator.evaluate_text(text)

# 打印结果
print(f"词熵: {entropy_results['word_entropy']}")
print(f"N-gram熵: {entropy_results['ngram_entropy']}")
print(f"语义熵: {entropy_results['semantic_entropy']}")
print(f"结构熵: {entropy_results['structural_entropy']}")
print(f"加权熵: {entropy_results['weighted_entropy']}")
```

## 模块交互

OpenKimi的核心模块之间的交互流程如下：

1. `KimiEngine`接收用户输入和配置，协调所有模块
2. `TextProcessor`处理文本并计算信息熵
3. `EntropyEvaluator`提供详细的熵计算方法
4. `RAGManager`存储低信息密度文本，并在需要时检索相关内容
5. `FrameworkGenerator`生成解决方案框架，并使用MPR策略生成最终答案

这种模块化设计使得OpenKimi能够灵活处理各种长文本需求，同时保持高质量的推理能力。 