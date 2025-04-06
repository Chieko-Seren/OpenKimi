import re
import math
import numpy as np
from collections import Counter
from typing import List, Dict, Tuple, Any, Optional

class TextProcessor:
    """文本处理器：负责文本分块和信息熵计算"""
    
    def __init__(self, batch_size: int = 512):
        """
        初始化文本处理器
        
        Args:
            batch_size: 文本分块的大小
        """
        self.batch_size = batch_size
    
    def split_into_batches(self, text: str) -> List[str]:
        """
        将文本按照batch_size分块
        
        Args:
            text: 输入文本
            
        Returns:
            分块后的文本列表
        """
        # 按照标点符号和空格分词
        words = re.findall(r'\w+|[^\w\s]', text)
        
        # 按照batch_size分块
        batches = []
        current_batch = []
        current_length = 0
        
        for word in words:
            if current_length + len(word) > self.batch_size and current_batch:
                batches.append(''.join(current_batch))
                current_batch = []
                current_length = 0
            
            current_batch.append(word)
            current_length += len(word)
        
        # 添加最后一个batch
        if current_batch:
            batches.append(''.join(current_batch))
            
        return batches
    
    def calculate_entropy(self, text: str) -> float:
        """
        计算文本的信息熵（基于字符频率）
        
        Args:
            text: 输入文本
            
        Returns:
            信息熵值
        """
        if not text:
            return 0.0
            
        # 计算字符频率而不是词频
        char_counts = Counter(text)
        total_chars = len(text)
        
        # 计算信息熵
        entropy = 0.0
        for char, count in char_counts.items():
            probability = count / total_chars
            entropy -= probability * math.log2(probability)
            
        return entropy
    
    def classify_by_entropy(self, batches: List[str], threshold: float = 3.0) -> Tuple[List[str], List[str]]:
        """
        根据信息熵将文本分为有用和不太有用的部分
        
        Args:
            batches: 分块后的文本列表
            threshold: 信息熵阈值，低于此值的块被视为不太有用
            
        Returns:
            (useful_batches, less_useful_batches): 有用和不太有用的文本块
        """
        useful_batches = []
        less_useful_batches = []
        
        for batch in batches:
            entropy = self.calculate_entropy(batch)
            if entropy >= threshold:
                useful_batches.append(batch)
            else:
                less_useful_batches.append(batch)
                
        return useful_batches, less_useful_batches 