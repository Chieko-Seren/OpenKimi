from typing import Dict, List, Any, Optional, Tuple
import os
import json

from openkimi.core.processor import TextProcessor
from openkimi.core.rag import RAGManager
from openkimi.core.framework import FrameworkGenerator
from openkimi.utils.llm_interface import LLMInterface, get_llm_interface

class KimiEngine:
    def __init__(self, 
                 config_path: Optional[str] = None, 
                 llm: Optional[str] = None,
                 batch_size: int = 512,
                 entropy_threshold: float = 3.0):
        """
        初始化Kimi引擎
        
        Args:
            config_path: 配置文件路径
            llm: LLM模型路径（可选，优先级高于配置文件）
            batch_size: 文本分块大小
            entropy_threshold: 信息熵阈值
        """
        # 加载配置
        self.config = self._load_config(config_path)
        
        # 如果提供了llm参数，覆盖配置
        if llm:
            if isinstance(llm, str):
                self.config["llm"]["type"] = "local"
                self.config["llm"]["model_path"] = llm
            elif isinstance(llm, dict):
                self.config["llm"] = llm
        
        # 更新配置中的批次大小和信息熵阈值
        self.config["processor"] = self.config.get("processor", {})
        self.config["processor"]["batch_size"] = batch_size
        self.config["processor"]["entropy_threshold"] = entropy_threshold
                
        # 初始化LLM接口
        self.llm_interface = get_llm_interface(self.config["llm"])
        
        # 初始化各个模块
        self.processor = TextProcessor(batch_size=batch_size)
        self.rag_manager = RAGManager(self.llm_interface)
        self.framework_generator = FrameworkGenerator(self.llm_interface)
        
        # 会话历史
        self.conversation_history = []
        
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """
        加载配置文件
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            配置字典
        """
        default_config = {
            "llm": {
                "type": "dummy"
            },
            "processor": {
                "batch_size": 512,
                "entropy_threshold": 3.0
            }
        }
        
        if not config_path:
            return default_config
            
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # 合并默认配置
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                    elif isinstance(value, dict):
                        for sub_key, sub_value in value.items():
                            if sub_key not in config[key]:
                                config[key][sub_key] = sub_value
                return config
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            return default_config
            
    def ingest(self, text: str) -> None:
        """
        摄入文本，进行预处理和RAG存储
        
        Args:
            text: 输入文本
        """
        # 文本分块
        batches = self.processor.split_into_batches(text)
        
        # 基于信息熵分类
        useful_batches, less_useful_batches = self.processor.classify_by_entropy(
            batches, 
            threshold=self.config["processor"]["entropy_threshold"]
        )
        
        # 将低信息熵文本存入RAG
        self.rag_manager.batch_store(less_useful_batches)
        
        # 将有用文本添加到会话历史（简化处理）
        self.conversation_history.append({
            "role": "system",
            "content": "\n".join(useful_batches)
        })
        
    def chat(self, query: str) -> str:
        """
        处理用户查询并生成回复
        
        Args:
            query: 用户输入的查询
            
        Returns:
            生成的回复
        """
        # 添加用户查询到会话历史
        self.conversation_history.append({
            "role": "user",
            "content": query
        })
        
        # 从RAG检索相关信息
        rag_context = self.rag_manager.retrieve(query)
        
        # 获取最近的会话内容作为上下文
        context = self._get_recent_context()
        
        # 生成解决问题的框架
        framework = self.framework_generator.generate_framework(query, context)
        
        # 使用框架生成解决方案
        solution = self.framework_generator.generate_solution(
            query, 
            framework, 
            useful_context=context, 
            rag_context=rag_context
        )
        
        # 添加回复到会话历史
        self.conversation_history.append({
            "role": "assistant",
            "content": solution
        })
        
        return solution
    
    def _get_recent_context(self, max_tokens: int = 2048) -> str:
        """
        获取最近的会话上下文
        
        Args:
            max_tokens: 最大上下文长度
            
        Returns:
            上下文文本
        """
        # Todo: 考虑token计数和更复杂的历史管理
        recent_messages = []
        total_length = 0
        
        for message in reversed(self.conversation_history):
            content = message["content"]
            total_length += len(content)
            
            if total_length > max_tokens:
                break
                
            recent_messages.append(f"{message['role']}: {content}")
            
        return "\n\n".join(reversed(recent_messages))
    
    def reset(self) -> None:
        """重置会话历史"""
        self.conversation_history = [] 