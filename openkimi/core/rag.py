from typing import Dict, List, Tuple, Any, Optional
import numpy as np
from openkimi.utils.llm_interface import LLMInterface

class RAGManager:
    """RAG管理器：负责存储和检索文本块"""
    
    def __init__(self, llm_interface: LLMInterface):
        """
        初始化RAG管理器
        
        Args:
            llm_interface: LLM接口，用于生成摘要
        """
        self.llm_interface = llm_interface
        self.rag_store: Dict[str, str] = {}  # 摘要 -> 原文本
        
    def summarize_text(self, text: str) -> str:
        """
        对文本进行摘要
        
        Args:
            text: 需要摘要的文本
            
        Returns:
            文本摘要
        """
        prompt = f"请对以下文本进行简短摘要，保留其核心信息点:\n\n{text}\n\n摘要:"
        summary = self.llm_interface.generate(prompt)
        return summary.strip()
    
    def store_text(self, text: str) -> str:
        """
        将文本存储到RAG中
        
        Args:
            text: 需要存储的文本
            
        Returns:
            文本摘要（作为RAG的key）
        """
        summary = self.summarize_text(text)
        self.rag_store[summary] = text
        return summary
    
    def batch_store(self, texts: List[str]) -> List[str]:
        """
        批量存储多个文本到RAG
        
        Args:
            texts: 需要存储的文本列表
            
        Returns:
            摘要列表
        """
        summaries = []
        for text in texts:
            summary = self.store_text(text)
            summaries.append(summary)
        return summaries
    
    def retrieve(self, query: str, top_k: int = 3) -> List[str]:
        """
        根据查询检索相关文本
        
        Args:
            query: 查询文本
            top_k: 返回的最大结果数量
            
        Returns:
            检索到的文本列表
        """
        if not self.rag_store:
            return []
            
        # Todo: 使用向量数据库和余弦相似度
        scores = []
        for summary, text in self.rag_store.items():
            # 计算查询与摘要的关键词重合度
            query_words = set(query.lower().split())
            summary_words = set(summary.lower().split())
            match_score = len(query_words.intersection(summary_words)) / max(len(query_words), 1)
            scores.append((summary, match_score))
            
        # 按相关性排序
        scores.sort(key=lambda x: x[1], reverse=True)
        
        # 返回top_k个最相关的文本
        results = []
        for summary, score in scores[:top_k]:
            if score > 0:  # 只返回有相关性的结果
                results.append(self.rag_store[summary])
                
        return results 