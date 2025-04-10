from typing import List, Dict, Optional, Union, AsyncGenerator, Any
from abc import ABC, abstractmethod
import os
import base64
from io import BytesIO
from PIL import Image
import numpy as np

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
        """生成包含图像理解的文本
        
        Args:
            prompt: 提示文本
            images: 图像列表，可以是文件路径、字节流或PIL图像对象
            max_tokens: 生成的最大token数量
            
        Returns:
            生成的文本
        """
        pass
        
    @abstractmethod
    async def stream_generate_with_images(
        self,
        prompt: str,
        images: List[Union[str, bytes, Image.Image]],
        max_tokens: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        """流式生成包含图像理解的文本
        
        Args:
            prompt: 提示文本
            images: 图像列表，可以是文件路径、字节流或PIL图像对象
            max_tokens: 生成的最大token数量
            
        Yields:
            生成的文本片段
        """
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
        
    @staticmethod
    def process_image(image: Union[str, bytes, Image.Image]) -> Union[str, bytes]:
        """处理图像，转换为模型可接受的格式
        
        Args:
            image: 输入图像，可以是文件路径、字节流或PIL图像对象
            
        Returns:
            处理后的图像，通常是base64编码字符串或字节流
        """
        # 如果是文件路径
        if isinstance(image, str):
            if os.path.isfile(image):
                with open(image, "rb") as f:
                    image_bytes = f.read()
                    return base64.b64encode(image_bytes).decode('utf-8')
            else:
                raise ValueError(f"图像文件路径不存在: {image}")
                
        # 如果是字节流
        elif isinstance(image, bytes):
            return base64.b64encode(image).decode('utf-8')
            
        # 如果是PIL图像对象
        elif isinstance(image, Image.Image):
            buffer = BytesIO()
            image.save(buffer, format="PNG")
            return base64.b64encode(buffer.getvalue()).decode('utf-8')
            
        else:
            raise TypeError(f"不支持的图像类型: {type(image)}")


class OpenAIMultiModalModel(MultiModalModel):
    """OpenAI多模态模型实现"""
    
    def __init__(
        self,
        api_key: str,
        model_name: str = "gpt-4-vision-preview",
        max_tokens_per_request: int = 4096,
        max_images: int = 10
    ):
        """初始化OpenAI多模态模型
        
        Args:
            api_key: OpenAI API密钥
            model_name: 模型名称
            max_tokens_per_request: 每次请求的最大token数量
            max_images: 每次请求支持的最大图像数量
        """
        import openai
        
        self.api_key = api_key
        self.model_name = model_name
        self.max_tokens_per_request = max_tokens_per_request
        self._max_images = max_images
        
        # 初始化OpenAI客户端
        self.client = openai.AsyncOpenAI(api_key=api_key)
        
    async def generate(self, prompt: str, max_tokens: Optional[int] = None) -> str:
        """生成文本
        
        Args:
            prompt: 提示文本
            max_tokens: 生成的最大token数量
            
        Returns:
            生成的文本
        """
        completion = await self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens or self.max_tokens_per_request
        )
        
        return completion.choices[0].message.content
        
    async def stream_generate(self, prompt: str, max_tokens: Optional[int] = None) -> AsyncGenerator[str, None]:
        """流式生成文本
        
        Args:
            prompt: 提示文本
            max_tokens: 生成的最大token数量
            
        Yields:
            生成的文本片段
        """
        stream = await self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens or self.max_tokens_per_request,
            stream=True
        )
        
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
                
    async def generate_with_images(
        self,
        prompt: str,
        images: List[Union[str, bytes, Image.Image]],
        max_tokens: Optional[int] = None
    ) -> str:
        """生成包含图像理解的文本
        
        Args:
            prompt: 提示文本
            images: 图像列表，可以是文件路径、字节流或PIL图像对象
            max_tokens: 生成的最大token数量
            
        Returns:
            生成的文本
        """
        if len(images) > self.max_images_per_request:
            raise ValueError(f"图像数量超过限制，最多支持{self.max_images_per_request}张图像")
            
        # 处理图像
        image_contents = []
        for image in images:
            image_data = self.process_image(image)
            image_contents.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_data}"
                    }
                }
            )
            
        # 构建消息
        messages = [
            {
                "role": "user",
                "content": [{"type": "text", "text": prompt}] + image_contents
            }
        ]
        
        # 发送请求
        completion = await self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            max_tokens=max_tokens or self.max_tokens_per_request
        )
        
        return completion.choices[0].message.content
        
    async def stream_generate_with_images(
        self,
        prompt: str,
        images: List[Union[str, bytes, Image.Image]],
        max_tokens: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        """流式生成包含图像理解的文本
        
        Args:
            prompt: 提示文本
            images: 图像列表，可以是文件路径、字节流或PIL图像对象
            max_tokens: 生成的最大token数量
            
        Yields:
            生成的文本片段
        """
        if len(images) > self.max_images_per_request:
            raise ValueError(f"图像数量超过限制，最多支持{self.max_images_per_request}张图像")
            
        # 处理图像
        image_contents = []
        for image in images:
            image_data = self.process_image(image)
            image_contents.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_data}"
                    }
                }
            )
            
        # 构建消息
        messages = [
            {
                "role": "user",
                "content": [{"type": "text", "text": prompt}] + image_contents
            }
        ]
        
        # 发送请求
        stream = await self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            max_tokens=max_tokens or self.max_tokens_per_request,
            stream=True
        )
        
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
                
    @property
    def supports_streaming(self) -> bool:
        """是否支持流式生成"""
        return True
        
    @property
    def max_context_length(self) -> int:
        """模型的最大上下文长度"""
        model_context_map = {
            "gpt-4-vision-preview": 128000,
            "gpt-4o": 128000,  # GPT-4o模型也支持图像
            "gpt-4-turbo": 128000,
            "gpt-4": 8192,
            "gpt-3.5-turbo": 4096
        }
        
        return model_context_map.get(self.model_name, 4096)
        
    @property
    def supports_image_input(self) -> bool:
        """是否支持图像输入"""
        return True
        
    @property
    def max_images_per_request(self) -> int:
        """每次请求支持的最大图像数量"""
        return self._max_images 