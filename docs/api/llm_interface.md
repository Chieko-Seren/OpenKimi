# LLMInterface

`LLMInterface` 是 OpenKimi 与底层大语言模型交互的统一接口，支持多种后端，包括测试用 dummy 模型、本地模型和 API 调用。

## 获取 LLM 接口

```python
from openkimi.utils.llm_interface import get_llm_interface

# 配置字典
llm_config = {
    "type": "api",  # 支持 "dummy", "local", "api"
    "api_key": "your-api-key",
    "model_name": "gpt-4"
}

# 获取接口实例
llm = get_llm_interface(llm_config)
```

## 支持的 LLM 后端

### Dummy 后端

用于测试和开发，不需要实际模型：

```python
llm_config = {
    "type": "dummy"
}
```

### 本地模型后端

使用 Hugging Face Transformers 加载本地模型：

```python
llm_config = {
    "type": "local",
    "model_path": "gpt2",  # 或其他本地模型路径
    "device": "auto",      # 可选："auto", "cpu", "cuda", "mps"
    "context_length": 2048 # 可选：模型上下文长度
}
```

### API 后端

使用 OpenAI 或兼容 API：

```python
llm_config = {
    "type": "api",
    "api_key": "your-api-key",           # 可选：从环境变量 OPENAI_API_KEY 读取
    "api_url": "https://api.openai.com", # 可选：从环境变量 OPENAI_API_BASE 读取
    "model_name": "gpt-4",
    "context_length": 8192               # 可选：模型上下文长度
}
```

## LLMInterface 类方法

### 调用模型生成文本

```python
response = llm.generate(prompt, max_tokens=100, temperature=0.7)
```

**参数:**
- **prompt** (`str`): 输入提示
- **max_tokens** (`int`, 可选): 生成的最大token数，默认为100
- **temperature** (`float`, 可选): 生成的随机性，默认为0.7

**返回:** `str` - 模型生成的文本

### 获取模型分词器

```python
tokenizer = llm.get_tokenizer()
```

**返回:** 模型的分词器对象

### 获取模型最大上下文长度

```python
max_context_length = llm.get_max_context_length()
```

**返回:** `int` - 模型的最大上下文长度（token数）

## 额外工具类

### TokenCounter

计算文本的token数量：

```python
from openkimi.utils.llm_interface import TokenCounter

# 使用模型分词器初始化
tokenizer = llm.get_tokenizer()
counter = TokenCounter(tokenizer)

# 计算文本token数
text = "这是一段示例文本"
token_count = counter.count_tokens(text)
print(f"Token 数量: {token_count}")
```

## 示例用法

### 简单文本生成

```python
from openkimi.utils.llm_interface import get_llm_interface

# 配置 API 后端
llm_config = {
    "type": "api",
    "model_name": "gpt-4"
}

# 获取 LLM 接口
llm = get_llm_interface(llm_config)

# 生成文本
prompt = "请解释量子计算的基本原理"
response = llm.generate(prompt, max_tokens=200)
print(response)
```

### 本地模型用法

```python
# 配置本地模型
llm_config = {
    "type": "local",
    "model_path": "meta-llama/Llama-2-7b-chat-hf",
    "device": "cuda"
}

# 获取 LLM 接口
llm = get_llm_interface(llm_config)

# 生成文本
prompt = "写一首关于人工智能的短诗"
response = llm.generate(prompt, temperature=0.9)
print(response)
```

## 多模型支持

OpenKimi 通过 LLMInterface 抽象层提供了统一的接口，使系统可以无缝切换不同的底层模型。未来还将支持更多模型和优化选项，如量化和加速推理。 