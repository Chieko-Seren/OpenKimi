from abc import ABC, abstractmethod
from typing import AsyncGenerator, Optional

class BaseModel(ABC):
    """模型抽象基类"""
    
    @abstractmethod
    async def generate(self, prompt: str, max_tokens: Optional[int] = None) -> str:
        """生成文本
        
        Args:
            prompt: 输入提示
            max_tokens: 最大生成token数
            
        Returns:
            生成的文本
        """
        pass
    
    @abstractmethod
    async def stream_generate(self, prompt: str, max_tokens: Optional[int] = None) -> AsyncGenerator[str, None]:
        """流式生成文本
        
        Args:
            prompt: 输入提示
            max_tokens: 最大生成token数
            
        Yields:
            生成的文本片段
        """
        pass
    
    @property
    @abstractmethod
    def supports_streaming(self) -> bool:
        """是否支持流式生成"""
        pass
    
    @property
    @abstractmethod
    def max_context_length(self) -> int:
        """最大上下文长度"""
        pass 