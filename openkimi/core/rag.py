from typing import Dict, List, Tuple, Any, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from openkimi.utils.llm_interface import LLMInterface
from openkimi.utils.prompt_loader import load_prompt

class RAGManager:
    """RAG管理器：负责存储和检索文本块"""
    
    def __init__(self, llm_interface: LLMInterface, embedding_model_name: str = 'all-MiniLM-L6-v2'):
        """
        初始化RAG管理器
        
        Args:
            llm_interface: LLM接口，用于生成摘要
            embedding_model_name: 用于生成文本嵌入的Sentence Transformer模型名称
        """
        self.llm_interface = llm_interface
        self.rag_store: Dict[str, str] = {}  # 摘要 -> 原文本
        self.summary_vectors: Dict[str, np.ndarray] = {} # 摘要 -> 向量
        self.embedding_model = SentenceTransformer(embedding_model_name)
        self.summarize_prompt_template = load_prompt('summarize')
        
    def summarize_text(self, text: str) -> str:
        """
        对文本进行摘要
        
        Args:
            text: 需要摘要的文本
            
        Returns:
            文本摘要
        """
        # Todo: Add recursive RAG logic if text is too long for summarization LLM
        prompt = self.summarize_prompt_template.format(text=text)
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
        if summary in self.rag_store: # Avoid duplicates, maybe update?
            return summary 
            
        self.rag_store[summary] = text
        # Generate and store embedding for the summary
        summary_embedding = self.embedding_model.encode(summary)
        self.summary_vectors[summary] = summary_embedding
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
        # Todo: Potentially optimize batch summarization and embedding generation
        for text in texts:
            summary = self.store_text(text)
            summaries.append(summary)
        return summaries
    
    def retrieve(self, query: str, top_k: int = 3) -> List[str]:
        """
        根据查询检索相关文本 (使用向量相似度)
        
        Args:
            query: 查询文本
            top_k: 返回的最大结果数量
            
        Returns:
            检索到的文本列表
        """
        if not self.rag_store or not self.summary_vectors:
            return []
            
        # Generate embedding for the query
        query_embedding = self.embedding_model.encode(query).reshape(1, -1)
        
        # Prepare summary embeddings
        summaries = list(self.summary_vectors.keys())
        summary_embeddings = np.array([self.summary_vectors[s] for s in summaries])

        if summary_embeddings.ndim == 1: # Handle case with only one stored item
            summary_embeddings = summary_embeddings.reshape(1, -1)
            
        # Calculate cosine similarities
        similarities = cosine_similarity(query_embedding, summary_embeddings)[0]
        
        # Get top_k indices
        top_k_indices = np.argsort(similarities)[::-1][:top_k]
        
        # Return the corresponding original texts
        results = [self.rag_store[summaries[i]] for i in top_k_indices if similarities[i] > 0] # Optionally add a threshold
        return results 