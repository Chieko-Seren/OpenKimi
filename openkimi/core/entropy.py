from typing import List, Dict, Optional, Union
import numpy as np
from collections import Counter
import math
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class EntropyEvaluator:
    """信息熵评估器，支持多种粒度的信息熵计算方法"""
    
    def __init__(
        self,
        use_tfidf: bool = True,
        ngram_range: tuple = (1, 2),
        max_features: int = 10000
    ):
        """初始化信息熵评估器
        
        Args:
            use_tfidf: 是否使用TF-IDF进行特征提取
            ngram_range: n-gram范围，用于特征提取
            max_features: 最大特征数量
        """
        self.use_tfidf = use_tfidf
        self.ngram_range = ngram_range
        self.max_features = max_features
        self.vectorizer = TfidfVectorizer(
            ngram_range=ngram_range,
            max_features=max_features
        ) if use_tfidf else None
        
    def calculate_word_entropy(self, text: str) -> float:
        """计算词级别的信息熵
        
        Args:
            text: 输入文本
            
        Returns:
            词级别的信息熵值
        """
        # 分词并计算词频
        words = text.lower().split()
        word_freq = Counter(words)
        total_words = len(words)
        
        # 计算信息熵
        entropy = 0
        for freq in word_freq.values():
            p = freq / total_words
            entropy -= p * math.log2(p)
            
        return entropy
        
    def calculate_ngram_entropy(self, text: str, n: int = 2) -> float:
        """计算n-gram级别的信息熵
        
        Args:
            text: 输入文本
            n: n-gram的大小
            
        Returns:
            n-gram级别的信息熵值
        """
        # 生成n-grams
        words = text.lower().split()
        ngrams = [tuple(words[i:i+n]) for i in range(len(words)-n+1)]
        
        # 计算n-gram频率
        ngram_freq = Counter(ngrams)
        total_ngrams = len(ngrams)
        
        # 计算信息熵
        entropy = 0
        for freq in ngram_freq.values():
            p = freq / total_ngrams
            entropy -= p * math.log2(p)
            
        return entropy
        
    def calculate_semantic_entropy(self, texts: List[str]) -> float:
        """计算语义级别的信息熵（基于TF-IDF和余弦相似度）
        
        Args:
            texts: 文本列表
            
        Returns:
            语义级别的信息熵值
        """
        if not self.use_tfidf or not texts:
            return 0.0
            
        # 使用TF-IDF提取特征
        tfidf_matrix = self.vectorizer.fit_transform(texts)
        
        # 计算文本间的余弦相似度
        similarities = cosine_similarity(tfidf_matrix)
        
        # 计算每个文本的语义熵
        semantic_entropies = []
        for i in range(len(texts)):
            # 获取当前文本与其他文本的相似度
            text_similarities = similarities[i]
            
            # 归一化相似度
            text_similarities = text_similarities / np.sum(text_similarities)
            
            # 计算信息熵
            entropy = -np.sum(text_similarities * np.log2(text_similarities + 1e-10))
            semantic_entropies.append(entropy)
            
        # 返回平均语义熵
        return np.mean(semantic_entropies)
        
    def calculate_structural_entropy(self, text: str) -> float:
        """计算结构级别的信息熵（基于句子长度和标点符号分布）
        
        Args:
            text: 输入文本
            
        Returns:
            结构级别的信息熵值
        """
        # 分割成句子
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        
        if not sentences:
            return 0.0
            
        # 计算句子长度分布
        lengths = [len(s.split()) for s in sentences]
        length_freq = Counter(lengths)
        total_sentences = len(sentences)
        
        # 计算句子长度的信息熵
        length_entropy = 0
        for freq in length_freq.values():
            p = freq / total_sentences
            length_entropy -= p * math.log2(p)
            
        # 计算标点符号分布
        punctuation = [c for c in text if c in '.,!?;:']
        punct_freq = Counter(punctuation)
        total_punct = len(punctuation)
        
        # 计算标点符号的信息熵
        punct_entropy = 0
        if total_punct > 0:
            for freq in punct_freq.values():
                p = freq / total_punct
                punct_entropy -= p * math.log2(p)
                
        # 返回结构熵（句子长度熵和标点符号熵的加权平均）
        return 0.7 * length_entropy + 0.3 * punct_entropy
        
    def evaluate_text(
        self,
        text: str,
        texts: Optional[List[str]] = None,
        weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, float]:
        """综合评估文本的信息熵
        
        Args:
            text: 要评估的文本
            texts: 用于语义熵计算的文本列表
            weights: 各类型熵的权重
            
        Returns:
            包含各种熵值的字典
        """
        # 默认权重
        default_weights = {
            'word': 0.3,
            'ngram': 0.2,
            'semantic': 0.3,
            'structural': 0.2
        }
        
        weights = weights or default_weights
        
        # 计算各种熵
        word_entropy = self.calculate_word_entropy(text)
        ngram_entropy = self.calculate_ngram_entropy(text)
        semantic_entropy = self.calculate_semantic_entropy([text] + (texts or []))
        structural_entropy = self.calculate_structural_entropy(text)
        
        # 计算加权平均熵
        weighted_entropy = (
            weights['word'] * word_entropy +
            weights['ngram'] * ngram_entropy +
            weights['semantic'] * semantic_entropy +
            weights['structural'] * structural_entropy
        )
        
        return {
            'word_entropy': word_entropy,
            'ngram_entropy': ngram_entropy,
            'semantic_entropy': semantic_entropy,
            'structural_entropy': structural_entropy,
            'weighted_entropy': weighted_entropy
        } 