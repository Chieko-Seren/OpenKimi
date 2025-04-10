import logging
import re
import math
import numpy as np
from collections import Counter
from typing import List, Dict, Tuple, Any, Optional
from .entropy import EntropyEvaluator

class TextProcessor:
    """文本处理器：负责文本分割、信息熵计算和文本块评估"""
    
    def __init__(
        self,
        batch_size: int = 512,
        entropy_threshold: float = 2.5,
        overlap_size: int = 50,
        entropy_method: str = "weighted"
    ):
        """
        初始化文本处理器
        
        Args:
            batch_size: 分块大小
            entropy_threshold: 低信息熵阈值，低于此值的块被认为不太重要
            overlap_size: 文本块重叠大小（以词为单位）
            entropy_method: 信息熵计算方法，可选值有"word"（词熵）、"ngram"（n-gram熵）、
                           "semantic"（语义熵）、"structural"（结构熵）、"weighted"（加权熵）
        """
        self.logger = logging.getLogger(__name__)
        self.batch_size = batch_size
        self.entropy_threshold = entropy_threshold
        self.overlap_size = overlap_size
        self.entropy_method = entropy_method
        self.entropy_evaluator = EntropyEvaluator()
    
    def split_into_batches(self, text: str, by_sentence: bool = True) -> List[str]:
        """
        将文本分割成固定大小的批次
        
        Args:
            text: 要分割的文本
            by_sentence: 是否尝试在句子边界分割
            
        Returns:
            分割后的文本块列表
        """
        # 分词
        words = text.split()
        
        # 如果by_sentence=True，尝试在句子边界分割
        if by_sentence:
            # 获取句子边界位置
            text_with_indices = []
            word_index = 0
            for word in words:
                if word.endswith(('.', '!', '?')):
                    text_with_indices.append((word_index, True))  # 标记为句子结束
                else:
                    text_with_indices.append((word_index, False))
                word_index += 1
            
            # 根据句子边界和batch_size切分
            batches = []
            start_idx = 0
            
            while start_idx < len(words):
                # 找出start_idx后的batch_size范围内的最近句子结束点
                end_idx = min(start_idx + self.batch_size, len(words))
                for i in range(min(start_idx + self.batch_size, len(words)) - 1, start_idx, -1):
                    if i < len(text_with_indices) and text_with_indices[i][1]:
                        end_idx = i + 1  # 在句子结束后切分
                        break
                
                # 如果找不到句子结束点，就按固定大小切分
                batches.append(' '.join(words[start_idx:end_idx]))
                
                # 更新起始位置，考虑overlap
                start_idx = max(0, end_idx - self.overlap_size)
        else:
            # 简单按固定大小切分，考虑overlap
            batches = []
            for i in range(0, len(words), self.batch_size - self.overlap_size):
                batches.append(' '.join(words[i:i + self.batch_size]))
        
        return batches
    
    def calculate_entropy(self, text: str, context_texts: Optional[List[str]] = None) -> Dict[str, float]:
        """
        计算文本的信息熵
        
        Args:
            text: 要计算熵的文本
            context_texts: 用于计算语义熵的上下文文本列表
            
        Returns:
            包含各类熵值的字典
        """
        # 使用增强型熵评估器计算熵
        result = self.entropy_evaluator.evaluate_text(text, context_texts)
        return result
    
    def classify_by_entropy(
        self, 
        batches: List[str], 
        threshold: Optional[float] = None,
        context_aware: bool = True
    ) -> Tuple[List[str], List[str]]:
        """
        根据信息熵对文本块进行分类
        
        Args:
            batches: 要分类的文本块列表
            threshold: 信息熵阈值，低于此值的块被认为信息密度低
            context_aware: 是否考虑上下文进行熵计算
            
        Returns:
            (信息密度高的块, 信息密度低的块)
        """
        if threshold is None:
            threshold = self.entropy_threshold
            
        # 计算每个块的熵值
        entropies = []
        for batch in batches:
            # 根据熵计算方法和是否考虑上下文，计算不同类型的熵
            context_texts = batches if context_aware else None
            entropy_results = self.calculate_entropy(batch, context_texts)
            
            # 根据指定的熵方法选择相应的熵值
            if self.entropy_method == "word":
                entropy = entropy_results["word_entropy"]
            elif self.entropy_method == "ngram":
                entropy = entropy_results["ngram_entropy"]
            elif self.entropy_method == "semantic":
                entropy = entropy_results["semantic_entropy"]
            elif self.entropy_method == "structural":
                entropy = entropy_results["structural_entropy"]
            else:  # weighted或其他情况
                entropy = entropy_results["weighted_entropy"]
                
            entropies.append(entropy)
            
        # 根据阈值分类
        useful_batches = []
        less_useful_batches = []
        
        for batch, entropy in zip(batches, entropies):
            if entropy >= threshold:
                useful_batches.append(batch)
            else:
                less_useful_batches.append(batch)
                
        self.logger.debug(f"文本分类完成。信息密度高的块：{len(useful_batches)}，信息密度低的块：{len(less_useful_batches)}")
        
        return useful_batches, less_useful_batches
        
    def get_batch_entropy_ranking(
        self, 
        batches: List[str], 
        context_aware: bool = True
    ) -> List[Tuple[str, float]]:
        """
        获取文本块的熵值排名
        
        Args:
            batches: 要排名的文本块列表
            context_aware: 是否考虑上下文进行熵计算
            
        Returns:
            按熵值排序的(文本块, 熵值)列表，从高到低
        """
        # 计算每个块的熵值
        batch_entropies = []
        for batch in batches:
            context_texts = batches if context_aware else None
            entropy_results = self.calculate_entropy(batch, context_texts)
            
            # 根据指定的熵方法选择相应的熵值
            if self.entropy_method == "word":
                entropy = entropy_results["word_entropy"]
            elif self.entropy_method == "ngram":
                entropy = entropy_results["ngram_entropy"]
            elif self.entropy_method == "semantic":
                entropy = entropy_results["semantic_entropy"]
            elif self.entropy_method == "structural":
                entropy = entropy_results["structural_entropy"]
            else:  # weighted或其他情况
                entropy = entropy_results["weighted_entropy"]
                
            batch_entropies.append((batch, entropy))
            
        # 按熵值从高到低排序
        batch_entropies.sort(key=lambda x: x[1], reverse=True)
        
        return batch_entropies
        
    def extract_key_segments(self, text: str, top_k: int = 3) -> List[str]:
        """
        提取文本中信息熵最高的片段
        
        Args:
            text: 要处理的文本
            top_k: 返回的片段数量
            
        Returns:
            信息熵最高的文本片段列表
        """
        # 分割文本
        batches = self.split_into_batches(text)
        
        # 获取熵值排名
        ranked_batches = self.get_batch_entropy_ranking(batches)
        
        # 返回top_k个信息熵最高的片段
        return [batch for batch, _ in ranked_batches[:top_k]] 