from typing import AsyncGenerator, Optional
import openai
from .base import BaseModel

class OpenAIModel(BaseModel):
    """OpenAI模型实现"""
    
    def __init__(self, api_key: str, model_name: str = "gpt-3.5-turbo"):
        """初始化OpenAI模型
        
        Args:
            api_key: OpenAI API密钥
            model_name: 模型名称
        """
        self.api_key = api_key
        self.model_name = model_name
        openai.api_key = api_key
        
    async def generate(self, prompt: str, max_tokens: Optional[int] = None) -> str:
        response = await openai.ChatCompletion.acreate(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens
        )
        return response.choices[0].message.content
        
    async def stream_generate(self, prompt: str, max_tokens: Optional[int] = None) -> AsyncGenerator[str, None]:
        response = await openai.ChatCompletion.acreate(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            stream=True
        )
        
        async for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
                
    @property
    def supports_streaming(self) -> bool:
        return True
        
    @property
    def max_context_length(self) -> int:
        # GPT-3.5-turbo的上下文长度为4096个token
        return 4096 