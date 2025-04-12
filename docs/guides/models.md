# 模型接口

OpenKimi提供了灵活的模型接口系统，支持不同类型的语言模型和多模态模型。本文档详细介绍模型接口的设计和使用方法。

## 基础模型接口

`BaseModel`是所有模型实现的抽象基类，定义了模型接口的基本方法。

### 接口定义

```python
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Optional

class BaseModel(ABC):
    """抽象基类：定义模型接口的基本方法"""
    
    @abstractmethod
    async def generate(self, prompt: str, max_tokens: Optional[int] = None) -> str:
        """生成文本"""
        pass
        
    @abstractmethod
    async def stream_generate(self, prompt: str, max_tokens: Optional[int] = None) -> AsyncGenerator[str, None]:
        """流式生成文本"""
        pass
        
    @property
    @abstractmethod
    def supports_streaming(self) -> bool:
        """是否支持流式生成"""
        pass
        
    @property
    @abstractmethod
    def max_context_length(self) -> int:
        """模型的最大上下文长度"""
        pass
```

### 主要方法

| 方法 | 描述 |
|------|------|
| `generate(prompt, max_tokens)` | 生成文本，接收提示和可选的最大token数 |
| `stream_generate(prompt, max_tokens)` | 流式生成文本，返回一个异步生成器 |
| `supports_streaming` (属性) | 返回模型是否支持流式生成 |
| `max_context_length` (属性) | 返回模型的最大上下文长度 |

## OpenAI模型实现

`OpenAIModel`是使用OpenAI API的模型实现。

### 使用方法

```python
from openkimi.core.models import OpenAIModel

# 初始化
model = OpenAIModel(
    api_key="your-api-key",  # OpenAI API密钥
    model_name="gpt-3.5-turbo"  # 可选，默认为"gpt-3.5-turbo"
)

# 生成文本
response = await model.generate("讲一个关于AI的故事", max_tokens=500)
print(response)

# 流式生成
async for chunk in model.stream_generate("讲一个关于AI的故事", max_tokens=500):
    print(chunk, end="")
```

### 特性

- 支持所有OpenAI模型（gpt-3.5-turbo、gpt-4等）
- 自动识别模型的最大上下文长度
- 支持流式生成

## 本地模型实现

`LocalModel`是使用本地加载的模型实现，支持HuggingFace Transformers模型。

### 使用方法

```python
from openkimi.core.models import LocalModel

# 初始化
model = LocalModel(
    model_path="meta-llama/Llama-2-7b-chat-hf",  # 模型路径或HF Hub ID
    device="cuda",  # 可选："auto", "cpu", "cuda", "mps"
    load_in_8bit=True,  # 是否启用8位量化
    load_in_4bit=False,  # 是否启用4位量化
    use_flash_attention=True,  # 是否使用FlashAttention
    use_accelerate=True  # 是否使用Accelerate
)

# 生成文本
response = await model.generate("讲一个关于AI的故事", max_tokens=500)
print(response)

# 流式生成
async for chunk in model.stream_generate("讲一个关于AI的故事", max_tokens=500):
    print(chunk, end="")
```

### 特性

- 支持Llama、Falcon、Mistral等开源模型
- 支持4位和8位量化，减少内存使用
- 支持Flash Attention加速
- 支持Accelerate进行多GPU分布式加载

## 多模态模型接口

`MultiModalModel`是基础模型接口的扩展，支持图像和文本输入。

### 接口定义

```python
from typing import List, Union
from PIL import Image
from .base import BaseModel

class MultiModalModel(BaseModel, ABC):
    """多模态模型基类，支持图像和文本输入"""
    
    @abstractmethod
    async def generate_with_images(
        self,
        prompt: str,
        images: List[Union[str, bytes, Image.Image]],
        max_tokens: Optional[int] = None
    ) -> str:
        """生成包含图像理解的文本"""
        pass
        
    @abstractmethod
    async def stream_generate_with_images(
        self,
        prompt: str,
        images: List[Union[str, bytes, Image.Image]],
        max_tokens: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        """流式生成包含图像理解的文本"""
        pass
        
    @property
    @abstractmethod
    def supports_image_input(self) -> bool:
        """是否支持图像输入"""
        pass
        
    @property
    @abstractmethod
    def max_images_per_request(self) -> int:
        """每次请求支持的最大图像数量"""
        pass
```

### 主要方法

| 方法 | 描述 |
|------|------|
| `generate_with_images(prompt, images, max_tokens)` | 生成包含图像理解的文本 |
| `stream_generate_with_images(prompt, images, max_tokens)` | 流式生成包含图像理解的文本 |
| `supports_image_input` (属性) | 返回模型是否支持图像输入 |
| `max_images_per_request` (属性) | 返回每次请求支持的最大图像数量 |

## OpenAI多模态模型实现

`OpenAIMultiModalModel`是使用OpenAI Vision API的多模态模型实现。

### 使用方法

```python
from openkimi.core.models import OpenAIMultiModalModel
from PIL import Image

# 初始化
model = OpenAIMultiModalModel(
    api_key="your-api-key",
    model_name="gpt-4-vision-preview",
    max_tokens_per_request=4096,
    max_images=10
)

# 加载图像
image1 = Image.open("image1.jpg")
image2 = "path/to/image2.jpg"  # 也可以使用文件路径

# 生成包含图像理解的文本
response = await model.generate_with_images(
    "描述这些图片中的内容",
    [image1, image2],
    max_tokens=500
)
print(response)

# 流式生成
async for chunk in model.stream_generate_with_images(
    "描述这些图片中的内容",
    [image1, image2],
    max_tokens=500
):
    print(chunk, end="")
```

### 特性

- 支持OpenAI的多模态模型（gpt-4-vision-preview等）
- 支持多种图像输入格式：PIL图像、文件路径、字节流
- 自动将图像转换为base64编码

## 模型工厂

OpenKimi提供了一个模型工厂函数，用于根据配置创建适当的模型实例。

### 使用方法

```python
from openkimi.core.models import create_model

# 使用本地模型
local_model_config = {
    "type": "local",
    "model_path": "meta-llama/Llama-2-7b-chat-hf",
    "device": "cuda",
    "load_in_8bit": True
}
local_model = create_model(local_model_config)

# 使用OpenAI API
api_model_config = {
    "type": "api",
    "api_key": "your-api-key",
    "model_name": "gpt-4"
}
api_model = create_model(api_model_config)

# 使用OpenAI多模态模型
multimodal_config = {
    "type": "multimodal",
    "api_key": "your-api-key",
    "model_name": "gpt-4-vision-preview"
}
multimodal_model = create_model(multimodal_config)
```

## 自定义模型实现

你可以通过继承`BaseModel`或`MultiModalModel`来实现自定义模型。

### 示例：自定义模型实现

```python
from openkimi.core.models import BaseModel
from typing import AsyncGenerator, Optional

class MyCustomModel(BaseModel):
    """自定义模型实现"""
    
    def __init__(self, model_path: str):
        self.model_path = model_path
        # 在这里初始化你的模型
        
    async def generate(self, prompt: str, max_tokens: Optional[int] = None) -> str:
        # 实现文本生成逻辑
        return "生成的文本"
        
    async def stream_generate(self, prompt: str, max_tokens: Optional[int] = None) -> AsyncGenerator[str, None]:
        # 实现流式生成逻辑
        chunks = ["生成", "的", "文本"]
        for chunk in chunks:
            yield chunk
            
    @property
    def supports_streaming(self) -> bool:
        return True
        
    @property
    def max_context_length(self) -> int:
        return 4096
```

## 注意事项

- 确保在使用本地模型时系统有足够的内存/显存
- 对于API模型，请确保有有效的API密钥和网络连接
- 多模态模型可能需要更多资源和更高的API费用
- 调用`generate`和`stream_generate`方法时要使用`await`关键字，因为它们是异步方法 