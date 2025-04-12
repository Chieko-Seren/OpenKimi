# 多路径推理 (MPR)

多路径推理 (Multi Path Reasoning, MPR) 是OpenKimi的核心功能之一，它通过生成多个候选解决方案来提高回答的全面性和准确性。本文档详细介绍MPR的概念、工作原理和使用方法。

## MPR概念

传统的LLM推理过程通常是单路径的：从输入到输出沿着一条路径进行。然而，对于复杂问题，单一路径可能会忽略某些重要方面或陷入局部最优解。

MPR通过以下方式解决这个问题：

1. 基于不同的上下文侧重生成多个候选解决方案
2. 使用不同的推理策略探索多条思路路径
3. 综合多个候选方案的优点，生成一个全面、平衡的最终答案

## MPR的工作原理

MPR在OpenKimi中的工作流程如下：

### 1. 上下文采样

首先，MPR使用不同的采样策略从可用上下文中选择信息。OpenKimi支持以下采样策略：

- **随机采样**：随机选择上下文片段，引入探索性
- **基于熵的采样**：偏向选择信息熵高的上下文片段
- **基于相关性的采样**：选择与查询最相关的上下文片段
- **基于多样性的采样**：确保选择的上下文片段相互之间有足够差异

### 2. 候选解决方案生成

对于每个采样的上下文，MPR生成一个候选解决方案。这些候选方案可能关注问题的不同方面或采用不同的思路。

### 3. 解决方案合成

最后，MPR使用一种合成策略将多个候选方案融合为一个最终答案。OpenKimi支持以下合成策略：

- **多数投票**：选择多个候选方案中出现频率最高的观点
- **加权平均**：根据每个候选方案的质量或相关性进行加权合成
- **层次合成**：将候选方案分解为组成部分，然后重新组合
- **共识构建**：识别所有候选方案中的共同点，构建核心共识

## 配置MPR

在OpenKimi中启用和配置MPR非常简单：

```python
from openkimi import KimiEngine

# 启用MPR并设置候选方案数量
engine = KimiEngine(mpr_candidates=3)
```

或者通过配置文件：

```json
{
    "llm": {
        "type": "api",
        "api_key": "your-api-key",
        "model_name": "gpt-4"
    },
    "processor": {
        "batch_size": 512
    },
    "rag": {
        "top_k": 5
    },
    "mpr_candidates": 3
}
```

默认情况下，`mpr_candidates=1`表示禁用MPR，只生成一个解决方案。

## 高级MPR配置

对于需要更精细控制的场景，可以直接使用`FrameworkGenerator`类：

```python
from openkimi.core import FrameworkGenerator
from openkimi.core.models import OpenAIModel

# 初始化模型
model = OpenAIModel(api_key="your-api-key")

# 初始化框架生成器
framework_gen = FrameworkGenerator(model)

# 生成框架
framework = await framework_gen.generate_framework(
    "如何改善城市空气质量？", 
    "上下文内容..."
)

# 使用MPR生成解决方案，自定义策略
solution = await framework_gen.generate_solution_mpr(
    query="如何改善城市空气质量？",
    framework=framework,
    useful_context="有用的上下文...",
    rag_context=["相关文本1", "相关文本2", "相关文本3"],
    num_candidates=4,  # 候选方案数量
    context_strategy="diversity",  # 上下文采样策略
    synthesis_strategy="hierarchical"  # 解决方案合成策略
)
```

## 上下文采样策略

选择合适的上下文采样策略对MPR的效果至关重要：

### 随机采样 (`"random"`)

```python
solution = await framework_gen.generate_solution_mpr(
    # 其他参数...
    context_strategy="random"
)
```

- **优点**：增加探索性，可能发现新思路
- **适用场景**：创意生成、思维发散、探索多种可能性

### 基于熵的采样 (`"entropy"`)

```python
solution = await framework_gen.generate_solution_mpr(
    # 其他参数...
    context_strategy="entropy"
)
```

- **优点**：优先选择信息密度高的上下文
- **适用场景**：信息密集型问题，需要高信息含量的分析

### 基于相关性的采样 (`"relevance"`)

```python
solution = await framework_gen.generate_solution_mpr(
    # 其他参数...
    context_strategy="relevance"
)
```

- **优点**：确保上下文与查询高度相关
- **适用场景**：事实型问题，需要精确相关信息

### 基于多样性的采样 (`"diversity"`)

```python
solution = await framework_gen.generate_solution_mpr(
    # 其他参数...
    context_strategy="diversity"
)
```

- **优点**：选择相互差异大的上下文，覆盖多个视角
- **适用场景**：需要多角度分析的复杂问题，默认策略

## 解决方案合成策略

选择合适的合成策略对最终答案的质量同样重要：

### 多数投票 (`"majority"`)

```python
solution = await framework_gen.generate_solution_mpr(
    # 其他参数...
    synthesis_strategy="majority"
)
```

- **优点**：选择最一致的观点，降低异常答案影响
- **适用场景**：需要保守、一致性高的答案

### 加权平均 (`"weighted"`)

```python
solution = await framework_gen.generate_solution_mpr(
    # 其他参数...
    synthesis_strategy="weighted"
)
```

- **优点**：根据质量分配权重，优质方案影响更大
- **适用场景**：候选方案质量差异明显

### 层次合成 (`"hierarchical"`)

```python
solution = await framework_gen.generate_solution_mpr(
    # 其他参数...
    synthesis_strategy="hierarchical"
)
```

- **优点**：保留每个方案的优势部分，组合成更全面的解决方案
- **适用场景**：复杂问题需要综合多方面考虑，默认策略

### 共识构建 (`"consensus"`)

```python
solution = await framework_gen.generate_solution_mpr(
    # 其他参数...
    synthesis_strategy="consensus"
)
```

- **优点**：关注共同点，构建核心共识
- **适用场景**：需要稳健、被广泛接受的答案

## MPR的最佳实践

### 候选方案数量选择

- **少量候选方案**（2-3个）：适合简单问题或资源受限情况
- **中等候选方案**（4-5个）：平衡质量和多样性，适合大多数场景
- **大量候选方案**（6个以上）：适合非常复杂的问题，但会增加计算成本

### 策略组合建议

| 问题类型 | 推荐上下文策略 | 推荐合成策略 |
|---------|--------------|------------|
| 事实查询 | `"relevance"` | `"majority"` |
| 创意生成 | `"random"` | `"weighted"` |
| 多角度分析 | `"diversity"` | `"hierarchical"` |
| 争议性话题 | `"diversity"` | `"consensus"` |
| 技术问题 | `"entropy"` | `"hierarchical"` |

### 性能与成本考量

MPR会增加API调用次数和计算成本。一般来说：

- 总API调用次数 ≈ 1 (框架生成) + N (候选方案) + 1 (合成)
- 处理时间和API成本约为普通生成的 N+2 倍

为平衡性能和质量，建议：
- 对于简单问题，使用`mpr_candidates=1`（禁用MPR）
- 对于中等复杂度问题，使用`mpr_candidates=3`
- 仅对复杂问题使用更多候选方案

## 示例：解决复杂问题

以下是使用MPR解决复杂问题的完整示例：

```python
import asyncio
from openkimi import KimiEngine

async def solve_complex_problem():
    # 初始化引擎，启用MPR
    engine = KimiEngine(
        llm_config={
            "type": "api",
            "api_key": "your-api-key",
            "model_name": "gpt-4"
        },
        mpr_candidates=5  # 使用5个候选方案
    )
    
    # 加载相关文档
    with open("climate_reports.txt", "r", encoding="utf-8") as f:
        text = f.read()
    
    # 摄入文本
    engine.ingest(text)
    
    # 提出复杂问题
    query = """
    考虑到最新的气候变化研究数据，分析城市规划如何适应未来气候变化，
    并提出具体的城市设计策略，同时考虑经济可行性、社会公平性和环境可持续性。
    """
    
    print(f"问题: {query}")
    print("生成回答中...\n")
    
    # 使用MPR生成答案
    response = await engine.chat(query)
    print(f"回答:\n{response}")

# 运行异步函数
asyncio.run(solve_complex_problem())
```

## 与其他技术的结合

MPR可以与OpenKimi的其他技术有效结合：

### 与递归RAG结合

```python
# MPR会自动触发递归RAG进行压缩，无需额外配置
engine = KimiEngine(
    llm_config={"type": "api", "api_key": "your-api-key"},
    mpr_candidates=3
)

# 即使文本超长，也能进行多路径推理
with open("very_long_document.txt", "r", encoding="utf-8") as f:
    engine.ingest(f.read())

response = engine.chat("复杂问题...")
```

### 与信息熵评估结合

```python
from openkimi.core import TextProcessor, EntropyEvaluator
from openkimi.core.models import OpenAIModel
from openkimi.core import FrameworkGenerator

# 初始化组件
model = OpenAIModel(api_key="your-api-key")
processor = TextProcessor(entropy_method="weighted")
framework_gen = FrameworkGenerator(model)

# 加载和处理文本
with open("document.txt", "r", encoding="utf-8") as f:
    text = f.read()

# 分割文本
batches = processor.split_into_batches(text)

# 根据熵评估排序
ranked_batches = processor.get_batch_entropy_ranking(batches)

# 提取高熵内容
high_entropy_content = "\n".join([batch for batch, _ in ranked_batches[:10]])

# 使用MPR生成解决方案
framework = await framework_gen.generate_framework("复杂问题", high_entropy_content)
solution = await framework_gen.generate_solution_mpr(
    "复杂问题", 
    framework, 
    useful_context=high_entropy_content,
    rag_context=[batch for batch, _ in ranked_batches[10:20]],
    num_candidates=3
)
```

## 总结

多路径推理是OpenKimi的核心功能，通过生成和综合多个候选解决方案来提高回答的全面性和准确性。通过配置不同的上下文采样策略和解决方案合成策略，可以适应各种复杂问题的需求。

MPR特别适合以下场景：
- 需要多角度分析的复杂问题
- 争议性话题需要平衡多种观点
- 创意生成需要探索多种可能性
- 需要高度准确和全面的技术分析

通过合理配置MPR参数，可以在答案质量和系统资源之间取得良好平衡。 