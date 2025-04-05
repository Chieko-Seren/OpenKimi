from typing import Dict, List, Any, Optional
import os
from abc import ABC, abstractmethod

class LLMInterface(ABC):
    """LLM接口抽象类，用于与不同的大语言模型交互"""
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """
        生成文本
        
        Args:
            prompt: 输入提示
            **kwargs: 其他参数
            
        Returns:
            生成的文本
        """
        pass

class DummyLLM(LLMInterface):
    def generate(self, prompt: str, **kwargs) -> str:
        pass # Todo

class LocalLLM(LLMInterface):
    """本地LLM模型接口"""
    
    def __init__(self, model_path: str):
        """
        初始化本地LLM
        
        Args:
            model_path: 模型路径
        """
        pass # Todo
        
    def generate(self, prompt: str, **kwargs) -> str:
        """
        使用本地模型生成文本
        
        Args:
            prompt: 输入提示
            **kwargs: 其他参数
            
        Returns:
            生成的文本
        """
        pass # Todo

class APIBasedLLM(LLMInterface):
    """基于API的LLM接口"""
    
    def __init__(self, api_key: str, api_url: str = None):
        """
        初始化API
        
        Args:
            api_key: API密钥
            api_url: API地址
        """
        self.api_key = api_key
        self.api_url = api_url or "https://api.example.com/v1/completions"
        
    def generate(self, prompt: str, **kwargs) -> str:
        """
        通过API生成文本
        
        Args:
            prompt: 输入提示
            **kwargs: 其他参数
            
        Returns:
            生成的文本
        """
        pass # Todo

def get_llm_interface(config: Dict[str, Any]) -> LLMInterface:
    """
    工厂函数，根据配置创建LLM接口
    
    Args:
        config: 配置字典
        
    Returns:
        LLM接口实例
    """
    llm_type = config.get("type", "dummy")
    
    if llm_type == "dummy":
        return DummyLLM()
    elif llm_type == "local":
        model_path = config.get("model_path")
        if not model_path:
            raise ValueError("本地LLM需要提供model_path")
        return LocalLLM(model_path)
    elif llm_type == "api":
        api_key = config.get("api_key") or os.environ.get("LLM_API_KEY")
        if not api_key:
            raise ValueError("API类型LLM需要提供api_key")
        return APIBasedLLM(api_key, config.get("api_url"))
    else:
        raise ValueError(f"不支持的LLM类型: {llm_type}") 