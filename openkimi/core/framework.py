from typing import List, Dict, Any
from openkimi.utils.llm_interface import LLMInterface
from openkimi.utils.prompt_loader import load_prompt
from .models.base import BaseModel
import random
import numpy as np

class FrameworkGenerator:
    """增强版框架生成器，支持多种MPR策略"""
    
    def __init__(self, model: BaseModel):
        self.model = model
        self.context_sampling_strategies = {
            "random": self._random_sampling,
            "entropy": self._entropy_based_sampling,
            "relevance": self._relevance_based_sampling,
            "diversity": self._diversity_based_sampling
        }
        self.solution_synthesis_strategies = {
            "majority": self._majority_vote,
            "weighted": self._weighted_average,
            "hierarchical": self._hierarchical_synthesis,
            "consensus": self._consensus_building
        }
        
    async def generate_framework(self, query: str, context: str) -> str:
        """生成解决方案框架"""
        prompt = f"""基于以下上下文，为问题"{query}"生成一个解决方案框架：
        
上下文：
{context}

请生成一个结构化的解决方案框架，包含以下部分：
1. 问题分析
2. 关键考虑因素
3. 解决步骤
4. 潜在挑战
5. 评估标准
"""
        return await self.model.generate(prompt)
        
    async def generate_solution_mpr(
        self,
        query: str,
        framework: str,
        useful_context: str,
        rag_context: List[str],
        num_candidates: int = 3,
        context_strategy: str = "diversity",
        synthesis_strategy: str = "hierarchical"
    ) -> str:
        """使用增强的MPR策略生成解决方案
        
        Args:
            query: 用户查询
            framework: 解决方案框架
            useful_context: 有用的上下文信息
            rag_context: RAG检索的上下文列表
            num_candidates: 候选方案数量
            context_strategy: 上下文采样策略
            synthesis_strategy: 解决方案合成策略
        """
        # 1. 使用选定的策略采样上下文
        sampled_contexts = self.context_sampling_strategies[context_strategy](
            useful_context, rag_context, num_candidates
        )
        
        # 2. 为每个采样的上下文生成候选解决方案
        candidates = []
        for ctx in sampled_contexts:
            prompt = f"""基于以下框架和上下文，为问题"{query}"生成一个详细的解决方案：

框架：
{framework}

上下文：
{ctx}

请生成一个完整的解决方案，确保：
1. 严格遵循框架结构
2. 充分利用上下文信息
3. 提供具体的实施建议
4. 考虑潜在的限制和解决方案
"""
            solution = await self.model.generate(prompt)
            candidates.append(solution)
            
        # 3. 使用选定的策略合成最终解决方案
        final_solution = self.solution_synthesis_strategies[synthesis_strategy](
            query, framework, candidates
        )
        
        return final_solution
        
    def _random_sampling(self, useful_context: str, rag_context: List[str], num_samples: int) -> List[str]:
        """随机采样上下文"""
        all_contexts = [useful_context] + rag_context
        return random.sample(all_contexts, min(num_samples, len(all_contexts)))
        
    def _entropy_based_sampling(self, useful_context: str, rag_context: List[str], num_samples: int) -> List[str]:
        """基于信息熵的上下文采样"""
        # 计算每个上下文片段的信息熵
        def calculate_entropy(text: str) -> float:
            # 简单的词频熵计算
            words = text.lower().split()
            word_freq = {}
            for word in words:
                word_freq[word] = word_freq.get(word, 0) + 1
            total_words = len(words)
            entropy = -sum((freq/total_words) * np.log2(freq/total_words) 
                         for freq in word_freq.values())
            return entropy
            
        all_contexts = [useful_context] + rag_context
        context_entropy = [(ctx, calculate_entropy(ctx)) for ctx in all_contexts]
        # 按熵值降序排序并选择前num_samples个
        context_entropy.sort(key=lambda x: x[1], reverse=True)
        return [ctx for ctx, _ in context_entropy[:num_samples]]
        
    def _relevance_based_sampling(self, useful_context: str, rag_context: List[str], num_samples: int) -> List[str]:
        """基于相关性的上下文采样"""
        # 这里可以实现更复杂的相关性计算，如使用embedding相似度
        # 当前使用简单的关键词匹配作为示例
        def calculate_relevance(text: str, query: str) -> float:
            query_words = set(query.lower().split())
            text_words = set(text.lower().split())
            return len(query_words & text_words) / len(query_words)
            
        all_contexts = [useful_context] + rag_context
        context_relevance = [(ctx, calculate_relevance(ctx, self.current_query)) 
                           for ctx in all_contexts]
        context_relevance.sort(key=lambda x: x[1], reverse=True)
        return [ctx for ctx, _ in context_relevance[:num_samples]]
        
    def _diversity_based_sampling(self, useful_context: str, rag_context: List[str], num_samples: int) -> List[str]:
        """基于多样性的上下文采样"""
        # 使用最大边际相关性(MMR)算法确保采样结果的多样性
        def calculate_similarity(text1: str, text2: str) -> float:
            # 简单的Jaccard相似度
            words1 = set(text1.lower().split())
            words2 = set(text2.lower().split())
            return len(words1 & words2) / len(words1 | words2)
            
        all_contexts = [useful_context] + rag_context
        selected = []
        remaining = all_contexts.copy()
        
        # 选择第一个样本（可以是随机的或基于其他标准）
        first = random.choice(remaining)
        selected.append(first)
        remaining.remove(first)
        
        # 迭代选择剩余样本
        while len(selected) < num_samples and remaining:
            # 计算每个剩余样本与已选样本的最大相似度
            max_similarities = []
            for ctx in remaining:
                similarities = [calculate_similarity(ctx, sel) for sel in selected]
                max_similarities.append((ctx, max(similarities)))
            
            # 选择相似度最小的样本
            next_sample = min(max_similarities, key=lambda x: x[1])[0]
            selected.append(next_sample)
            remaining.remove(next_sample)
            
        return selected
        
    def _majority_vote(self, query: str, framework: str, candidates: List[str]) -> str:
        """多数投票合成策略"""
        # 将候选方案分成段落
        paragraphs = [sol.split('\n\n') for sol in candidates]
        
        # 对每个段落位置进行多数投票
        final_paragraphs = []
        max_paragraphs = max(len(p) for p in paragraphs)
        
        for i in range(max_paragraphs):
            # 收集当前位置的所有段落
            current_paragraphs = [p[i] if i < len(p) else "" for p in paragraphs]
            # 选择最常见的非空段落
            non_empty = [p for p in current_paragraphs if p.strip()]
            if non_empty:
                final_paragraphs.append(max(set(non_empty), key=non_empty.count))
                
        return '\n\n'.join(final_paragraphs)
        
    def _weighted_average(self, query: str, framework: str, candidates: List[str]) -> str:
        """加权平均合成策略"""
        # 为每个候选方案分配权重（可以基于质量评估或其他标准）
        weights = [1.0] * len(candidates)  # 这里使用均匀权重，可以改进
        
        # 将候选方案分成句子
        sentences = [sol.split('. ') for sol in candidates]
        
        # 对每个句子位置进行加权平均
        final_sentences = []
        max_sentences = max(len(s) for s in sentences)
        
        for i in range(max_sentences):
            # 收集当前位置的所有句子
            current_sentences = [s[i] if i < len(s) else "" for s in sentences]
            # 选择权重最高的非空句子
            non_empty = [(s, w) for s, w in zip(current_sentences, weights) if s.strip()]
            if non_empty:
                final_sentences.append(max(non_empty, key=lambda x: x[1])[0])
                
        return '. '.join(final_sentences)
        
    def _hierarchical_synthesis(self, query: str, framework: str, candidates: List[str]) -> str:
        """分层合成策略"""
        # 将解决方案分成不同层次（如：概述、详细说明、具体建议等）
        levels = {
            "overview": [],
            "details": [],
            "recommendations": []
        }
        
        # 对每个候选方案进行分类
        for candidate in candidates:
            paragraphs = candidate.split('\n\n')
            if paragraphs:
                levels["overview"].append(paragraphs[0])
                if len(paragraphs) > 1:
                    levels["details"].extend(paragraphs[1:-1])
                if len(paragraphs) > 2:
                    levels["recommendations"].append(paragraphs[-1])
                    
        # 对每个层次进行合成
        final_solution = []
        
        # 合成概述（使用多数投票）
        if levels["overview"]:
            final_solution.append(max(set(levels["overview"]), 
                                   key=levels["overview"].count))
            
        # 合成详细说明（使用加权平均）
        if levels["details"]:
            final_solution.extend(self._weighted_average(query, framework, levels["details"]))
            
        # 合成建议（使用多数投票）
        if levels["recommendations"]:
            final_solution.append(max(set(levels["recommendations"]), 
                                   key=levels["recommendations"].count))
            
        return '\n\n'.join(final_solution)
        
    def _consensus_building(self, query: str, framework: str, candidates: List[str]) -> str:
        """共识构建合成策略"""
        # 1. 识别共同主题和关键点
        common_themes = self._identify_common_themes(candidates)
        
        # 2. 构建共识框架
        consensus_framework = self._build_consensus_framework(common_themes)
        
        # 3. 整合各个候选方案的优点
        integrated_solution = self._integrate_solutions(candidates, consensus_framework)
        
        return integrated_solution
        
    def _identify_common_themes(self, candidates: List[str]) -> List[str]:
        """识别候选方案中的共同主题"""
        # 提取关键词和短语
        themes = set()
        for candidate in candidates:
            # 这里可以使用更复杂的主题提取算法
            words = candidate.lower().split()
            themes.update(words)
            
        return list(themes)
        
    def _build_consensus_framework(self, themes: List[str]) -> str:
        """基于共同主题构建共识框架"""
        return "基于共同主题的解决方案框架：\n" + "\n".join(f"- {theme}" for theme in themes)
        
    def _integrate_solutions(self, candidates: List[str], framework: str) -> str:
        """整合各个候选方案的优点"""
        # 这里可以实现更复杂的整合逻辑
        # 当前使用简单的拼接作为示例
        return framework + "\n\n整合的解决方案：\n" + "\n\n".join(candidates) 