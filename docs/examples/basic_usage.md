# 基本用法示例

本文档提供OpenKimi的基本用法示例。

## 初始化引擎

```python
from openkimi import KimiEngine

# 使用默认配置初始化
engine = KimiEngine()

# 使用配置文件初始化
engine = KimiEngine(config_path="config.json")

# 使用参数初始化
engine = KimiEngine(
    llm_config={
        "type": "api",
        "api_key": "your-api-key",
        "model_name": "gpt-3.5-turbo"
    },
    processor_config={
        "batch_size": 512,
        "entropy_threshold": 2.5
    },
    rag_config={
        "embedding_model": "all-MiniLM-L6-v2",
        "top_k": 5
    },
    mpr_candidates=3
)
```

## 加载文本

```python
# 从文件加载
with open("document.txt", "r", encoding="utf-8") as f:
    engine.ingest(f.read())

# 直接加载字符串
long_text = """
这是一段很长的文本，包含了大量信息...
可能是一篇论文、小说或者技术文档...
"""
engine.ingest(long_text)
```

## 提问和回答

```python
# 简单提问
response = engine.chat("根据文档，总结主要内容")
print(response)

# 多轮对话
response1 = engine.chat("文档中提到了哪些关键技术？")
print(f"回答1: {response1}")

response2 = engine.chat("这些技术之间有什么关联？")
print(f"回答2: {response2}")

# 重置会话历史
engine.reset()
```

## 流式生成

```python
import asyncio

async def stream_example():
    # 初始化引擎
    engine = KimiEngine()
    
    # 加载文本
    with open("document.txt", "r", encoding="utf-8") as f:
        engine.ingest(f.read())
    
    # 流式生成
    print("问题: 文档的主要论点是什么？")
    print("回答: ", end="", flush=True)
    
    async for chunk in engine.stream_chat("文档的主要论点是什么？"):
        print(chunk, end="", flush=True)
    
    print()  # 打印最后的换行

# 运行异步函数
asyncio.run(stream_example())
```

## 不同模型的使用

### 使用OpenAI API

```python
from openkimi import KimiEngine

# 使用OpenAI API
engine = KimiEngine(
    llm_config={
        "type": "api",
        "api_key": "your-api-key",  # 或者从环境变量 OPENAI_API_KEY 读取
        "model_name": "gpt-4"
    }
)

# 加载文本并提问
engine.ingest("这是需要分析的文本...")
response = engine.chat("分析这段文本的写作风格")
print(response)
```

### 使用本地模型

```python
from openkimi import KimiEngine

# 使用本地模型
engine = KimiEngine(
    llm_config={
        "type": "local",
        "model_path": "meta-llama/Llama-2-7b-chat-hf",  # HF Hub ID
        "device": "cuda",  # 或 "cpu", "mps"
        "load_in_8bit": True  # 使用8位精度降低内存占用
    }
)

# 加载文本并提问
engine.ingest("这是需要分析的文本...")
response = engine.chat("分析这段文本的写作风格")
print(response)
```

## 系统监视与控制

使用Python的logging模块监视系统操作：

```python
import logging
import sys

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# 初始化引擎
from openkimi import KimiEngine
engine = KimiEngine()

# 运行任务
engine.ingest("文本内容...")
response = engine.chat("问题")
```

## 保存和恢复状态

```python
import pickle
from openkimi import KimiEngine

# 初始化引擎
engine = KimiEngine()
engine.ingest("文本内容...")

# 保存状态
with open("engine_state.pkl", "wb") as f:
    pickle.dump({
        "conversation_history": engine.conversation_history,
        # 其他需要保存的状态...
    }, f)

# 恢复状态
with open("engine_state.pkl", "rb") as f:
    state = pickle.load(f)
    
new_engine = KimiEngine()
new_engine.conversation_history = state["conversation_history"]
# 恢复其他状态...
```

## 完整示例应用

以下是一个完整的命令行应用示例，用于处理文档并回答问题：

```python
import argparse
import asyncio
from openkimi import KimiEngine

async def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="OpenKimi文档助手")
    parser.add_argument("--config", default=None, help="配置文件路径")
    parser.add_argument("--document", required=True, help="要处理的文档路径")
    parser.add_argument("--interactive", action="store_true", help="启用交互模式")
    parser.add_argument("--question", help="要回答的问题")
    args = parser.parse_args()
    
    # 初始化引擎
    print("初始化OpenKimi引擎...")
    engine = KimiEngine(config_path=args.config)
    
    # 加载文档
    print(f"加载文档: {args.document}")
    with open(args.document, "r", encoding="utf-8") as f:
        document_text = f.read()
    
    engine.ingest(document_text)
    print("文档加载完成！")
    
    # 单次问题模式
    if args.question and not args.interactive:
        print(f"\n问题: {args.question}")
        print("回答: ", end="", flush=True)
        
        async for chunk in engine.stream_chat(args.question):
            print(chunk, end="", flush=True)
        
        print("\n")
        return
    
    # 交互模式
    if args.interactive:
        print("\n=== 交互模式 ===")
        print("输入问题，或者输入'exit'退出")
        
        while True:
            question = input("\n问题: ")
            if question.lower() == "exit":
                break
            
            print("回答: ", end="", flush=True)
            async for chunk in engine.stream_chat(question):
                print(chunk, end="", flush=True)
            
            print()

if __name__ == "__main__":
    asyncio.run(main())
```

使用示例：

```bash
# 单次问题模式
python document_assistant.py --document paper.txt --question "这篇论文的主要贡献是什么？"

# 交互模式
python document_assistant.py --document paper.txt --interactive

# 使用配置文件
python document_assistant.py --config config.json --document paper.txt --interactive
```

## 注意事项

- 对于非常长的文档，处理可能需要一些时间
- 对于本地模型，确保有足够的内存或GPU内存
- 每次调用`engine.ingest()`都会重新处理文本
- 使用`engine.reset()`会清除会话历史，但不会清除摄入的文档

## 下一步

- 尝试[长文本处理示例](long_text_processing.md)
- 了解[多模态输入示例](multimodal_input.md)
- 探索更高级的[MPR策略](../guides/mpr.md) 