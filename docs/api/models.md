# 模型 API 参考

本页详细介绍 `openkimi.core.models` 模块中的类。

## BaseModel

所有模型实现的抽象基类。

```python
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Optional

class BaseModel(ABC):
    @abstractmethod
    async def generate(self, prompt: str, max_tokens: Optional[int] = None) -> str:
        pass
        
    @abstractmethod
    async def stream_generate(self, prompt: str, max_tokens: Optional[int] = None) -> AsyncGenerator[str, None]:
        pass
        
    @property
    @abstractmethod
    def supports_streaming(self) -> bool:
        pass
        
    @property
    @abstractmethod
    def max_context_length(self) -> int:
        pass
```

- `generate`: 异步方法，生成文本。
- `stream_generate`: 异步生成器，流式生成文本。
- `supports_streaming` (属性): 返回模型是否支持流式生成。
- `max_context_length` (属性): 返回模型的最大上下文长度。

## MultiModalModel

多模态模型实现的抽象基类，继承自`BaseModel`。

```python
from typing import List, Union
from PIL import Image

class MultiModalModel(BaseModel, ABC):
    @abstractmethod
    async def generate_with_images(self,
                                     prompt: str,
                                     images: List[Union[str, bytes, Image.Image]],
                                     max_tokens: Optional[int] = None) -> str:
        pass
        
    @abstractmethod
    async def stream_generate_with_images(self,
                                            prompt: str,
                                            images: List[Union[str, bytes, Image.Image]],
                                            max_tokens: Optional[int] = None) -> AsyncGenerator[str, None]:
        pass
        
    @property
    @abstractmethod
    def supports_image_input(self) -> bool:
        pass
        
    @property
    @abstractmethod
    def max_images_per_request(self) -> int:
        pass
        
    @staticmethod
    def process_image(image: Union[str, bytes, Image.Image]) -> Union[str, bytes]:
        pass
```

- `generate_with_images`: 异步方法，生成包含图像理解的文本。
- `stream_generate_with_images`: 异步生成器，流式生成包含图像理解的文本。
- `supports_image_input` (属性): 返回模型是否支持图像输入。
- `max_images_per_request` (属性): 返回每次请求支持的最大图像数量。
- `process_image` (静态方法): 处理图像（路径、字节流、PIL对象）为模型可接受的格式（通常是base64编码的字符串）。

## OpenAIModel

使用OpenAI API的`BaseModel`实现。

```python
class OpenAIModel(BaseModel):
    def __init__(self,
                 api_key: str,
                 model_name: str = "gpt-3.5-turbo"):
        pass
        
    # 实现了BaseModel的所有抽象方法
```

- `__init__`: 初始化模型，需要API密钥和可选的模型名称。

## LocalModel

使用本地HuggingFace Transformers模型的`BaseModel`实现。

```python
class LocalModel(BaseModel):
    def __init__(self,
                 model_path: str,
                 device: str = "auto",
                 load_in_8bit: bool = False,
                 load_in_4bit: bool = False,
                 use_flash_attention: bool = False,
                 use_accelerate: bool = False):
        pass
        
    # 实现了BaseModel的所有抽象方法
```

- `__init__`: 初始化模型，需要模型路径和各种可选的加载/优化参数。详细说明见[配置指南](../guides/configuration.md)。

## OpenAIMultiModalModel

使用OpenAI Vision API的`MultiModalModel`实现。

```python
class OpenAIMultiModalModel(MultiModalModel):
    def __init__(self,
                 api_key: str,
                 model_name: str = "gpt-4-vision-preview",
                 max_tokens_per_request: int = 4096,
                 max_images: int = 10):
        pass
        
    # 实现了MultiModalModel的所有抽象方法
    # 同时覆盖了BaseModel的方法以适应多模态场景
```

- `__init__`: 初始化模型，需要API密钥和可选的模型名称、最大token数、最大图像数。

## Model Factory (`create_model`)

根据配置字典创建适当模型实例的工厂函数。

```python
from typing import Dict, Any

def create_model(model_config: Dict[str, Any]) -> Optional[BaseModel]:
    pass
```

- **参数**：
    - `model_config` (Dict): 模型配置字典，结构见[配置指南](../guides/configuration.md)。需要包含`"type"`键来指定模型类型（`"api"`, `"local"`, `"multimodal"`）。
- **返回**：
    - 相应的`BaseModel`或`MultiModalModel`实例或`None`（如果配置无效）。 