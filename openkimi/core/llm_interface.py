import asyncio
import logging

logger = logging.getLogger(__name__)

class LLMInterface:
    def __init__(self, model):
        self.model = model

    def _check_context_length(self, prompt):
        # Implementation of _check_context_length method
        pass

    def _truncate_context(self, prompt):
        # Implementation of _truncate_context method
        pass

    async def _call_model(self, prompt, **kwargs):
        # Implementation of _call_model method
        pass

    async def generate(self, prompt: str, **kwargs) -> str:
        """
        生成文本回复
        
        Args:
            prompt: 输入提示
            **kwargs: 其他参数
            
        Returns:
            str: 生成的文本
        """
        try:
            # 检查上下文长度
            if not self._check_context_length(prompt):
                logger.warning("Context length exceeds maximum, truncating...")
                prompt = self._truncate_context(prompt)
            
            # 调用底层模型生成
            response = await self._call_model(prompt, **kwargs)
            return response
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            raise
            
    async def stream_generate(self, prompt: str, **kwargs):
        """
        流式生成文本回复
        
        Args:
            prompt: 输入提示
            **kwargs: 其他参数
            
        Yields:
            str: 生成的文本片段
        """
        try:
            # 检查上下文长度
            if not self._check_context_length(prompt):
                logger.warning("Context length exceeds maximum, truncating...")
                prompt = self._truncate_context(prompt)
            
            # 检查模型是否支持流式生成
            if hasattr(self.model, 'stream_generate'):
                async for chunk in self.model.stream_generate(prompt, **kwargs):
                    yield chunk
            else:
                # 如果不支持流式生成，则使用普通生成并模拟流式输出
                response = await self._call_model(prompt, **kwargs)
                # 每10个字符发送一次
                for i in range(0, len(response), 10):
                    chunk = response[i:i+10]
                    yield chunk
                    await asyncio.sleep(0.05)  # 添加小延迟以模拟流式输出
                    
        except Exception as e:
            logger.error(f"Error in stream generation: {str(e)}")
            raise 