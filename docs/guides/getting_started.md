# 快速入门

本指南将帮助你快速上手OpenKimi，通过一个简单的例子了解其基本功能和使用方法。

## 安装

首先，确保你已经安装了OpenKimi。如果尚未安装，请参考[安装指南](installation.md)：

```bash
pip install openkimi
```

## 基本用法

以下是使用OpenKimi的基本步骤：

### 1. 导入并初始化

```python
from openkimi import KimiEngine

# 使用默认配置初始化引擎
engine = KimiEngine()

# 或者使用自定义配置
# engine = KimiEngine(
#     llm_config={"type": "local", "model_path": "gpt2"},
#     processor_config={"batch_size": 256, "entropy_threshold": 2.5},
#     rag_config={"embedding_model": "all-MiniLM-L6-v2", "top_k": 5},
#     mpr_candidates=3
# )
```

### 2. 加载长文本

```python
# 加载一个较长的文本文件
with open("long_document.txt", "r", encoding="utf-8") as f:
    long_text = f.read()

# 将文本添加到引擎中
engine.ingest(long_text)
```

### 3. 提问并获取回答

```python
# 基于摄入的文本进行提问
response = engine.chat("根据文档内容，请总结主要观点")
print(response)
```

### 4. 流式响应（可选）

```python
# 使用流式API获取实时反馈
import asyncio

async def stream_example():
    async for chunk in engine.stream_chat("根据文档内容，请分析文本的结构"):
        print(chunk, end="", flush=True)
    print()  # 最后打印一个换行

# 运行异步函数
asyncio.run(stream_example())
```

## 完整示例

下面是一个完整的示例，演示如何使用OpenKimi处理《三体》小说的一部分并进行深度分析：

```python
import asyncio
from openkimi import KimiEngine

# 自定义配置
config = {
    "llm": {
        "type": "api",  # 使用OpenAI API
        "api_key": "your-api-key-here",  # 你的API密钥
        "model_name": "gpt-3.5-turbo"  # 使用的模型
    },
    "processor": {
        "batch_size": 512,  # 文本分块大小
        "entropy_threshold": 2.8  # 信息熵阈值
    },
    "rag": {
        "embedding_model": "all-MiniLM-L6-v2",  # 嵌入模型
        "top_k": 5  # 检索时返回的相关文本块数量
    },
    "mpr_candidates": 3  # 启用MPR，生成3个候选方案
}

# 初始化引擎
engine = KimiEngine(config_path=None, llm_config=config["llm"], 
                    processor_config=config["processor"],
                    rag_config=config["rag"],
                    mpr_candidates=config["mpr_candidates"])

# 加载三体小说片段
with open("santi_excerpt.txt", "r", encoding="utf-8") as f:
    novel_text = f.read()

# 摄入文本
engine.ingest(novel_text)
print("文本已成功摄入！")

# 提问
question = "请分析《三体》中的黑暗森林理论，并解释其主要隐喻"
print(f"问题: {question}")

# 获取回答
response = engine.chat(question)
print(f"回答: {response}")

# 使用流式API
async def stream_response():
    question2 = "叶文洁的心理变化经历了怎样的过程？"
    print(f"\n问题2: {question2}")
    print("流式回答: ", end="")
    async for chunk in engine.stream_chat(question2):
        print(chunk, end="", flush=True)
    print()

# 运行异步函数
asyncio.run(stream_response())
```

## 注意事项

- 对于大型文本，内存使用量可能会很高，请确保系统有足够的内存
- 首次加载大型文本时，处理可能需要一些时间
- 如果使用本地模型，确保有足够的GPU内存或配置适当的量化参数

## 下一步

- 了解OpenKimi的[配置选项](configuration.md)
- 探索[核心模块](core_modules.md)的详细功能
- 查看更多[示例](../examples/)来了解高级用法 