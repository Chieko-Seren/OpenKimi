from typing import Dict, List, Tuple, Any, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import logging
import traceback

# 导入FAISS库
try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logging.getLogger(__name__).warning("FAISS库未安装，将回退使用sklearn进行向量检索。推荐安装FAISS以获得更好的性能：pip install faiss-cpu")

from openkimi.utils.llm_interface import LLMInterface
from openkimi.utils.prompt_loader import load_prompt

class RAGManager:
    """RAG管理器：负责存储和检索文本块，使用FAISS进行高效向量检索"""
    
    def __init__(self, llm_interface: LLMInterface, embedding_model_name: str = 'all-MiniLM-L6-v2', use_faiss: bool = True):
        """
        初始化RAG管理器
        
        Args:
            llm_interface: LLM接口，用于生成摘要
            embedding_model_name: 用于生成文本嵌入的Sentence Transformer模型名称
            use_faiss: 是否使用FAISS索引（如果可用）
        """
        self.logger = logging.getLogger(__name__)
        
        if llm_interface is None:
            self.logger.error("RAGManager初始化失败: llm_interface为None")
            raise ValueError("LLM接口不能为None")
            
        self.llm_interface = llm_interface
        self.rag_store: Dict[str, str] = {}  # 摘要 -> 原文本
        self.summary_vectors: Dict[str, np.ndarray] = {} # 摘要 -> 向量
        self.summaries_list: List[str] = []  # 保存摘要顺序，便于FAISS检索后映射
        self.use_faiss = use_faiss and FAISS_AVAILABLE
        self.index = None  # FAISS索引
        self.vector_dimension = None  # 向量维度，由embedding模型决定
        
        # 尝试加载embedding模型
        try:
            self.logger.info(f"正在加载embedding模型: {embedding_model_name}")
            self.embedding_model = SentenceTransformer(embedding_model_name)
            self.logger.info("Embedding模型加载成功")
            
            # 确定向量维度
            test_vector = self.embedding_model.encode("测试文本")
            self.vector_dimension = len(test_vector)
            self.logger.info(f"向量维度: {self.vector_dimension}")
            
            # 初始化FAISS索引
            if self.use_faiss:
                self._initialize_faiss_index()
                
        except Exception as e:
            self.logger.error(f"加载embedding模型时出错: {e}")
            traceback.print_exc()
            # 尝试使用备用模型
            try:
                self.logger.info("尝试加载备用embedding模型: paraphrase-MiniLM-L3-v2")
                self.embedding_model = SentenceTransformer('paraphrase-MiniLM-L3-v2')
                
                # 确定向量维度
                test_vector = self.embedding_model.encode("测试文本")
                self.vector_dimension = len(test_vector)
                self.logger.info(f"向量维度: {self.vector_dimension}")
                
                # 初始化FAISS索引
                if self.use_faiss:
                    self._initialize_faiss_index()
                    
                self.logger.info("备用embedding模型加载成功")
            except Exception as e2:
                self.logger.error(f"加载备用embedding模型时出错: {e2}")
                traceback.print_exc()
                raise RuntimeError(f"无法加载任何embedding模型: {e2}")
        
        # 加载摘要提示模板
        try:
            self.summarize_prompt_template = load_prompt('summarize')
        except Exception as e:
            self.logger.error(f"加载摘要提示模板时出错: {e}")
            # 使用硬编码的备用提示模板
            self.logger.info("使用硬编码的备用摘要提示模板")
            self.summarize_prompt_template = """请对以下文本进行简洁的摘要，保留关键信息:

{text}

摘要:"""
    
    def _initialize_faiss_index(self):
        """初始化FAISS索引"""
        if not self.use_faiss or not FAISS_AVAILABLE:
            self.logger.warning("不使用FAISS索引，将回退到sklearn进行向量检索")
            return
            
        try:
            # 创建一个L2距离的索引(欧几里得距离)
            self.index = faiss.IndexFlatL2(self.vector_dimension)
            # 或者使用内积来近似余弦相似度(需要先归一化向量)
            # self.index = faiss.IndexFlatIP(self.vector_dimension)
            self.logger.info(f"FAISS索引初始化成功，类型: IndexFlatL2, 维度: {self.vector_dimension}")
        except Exception as e:
            self.logger.error(f"初始化FAISS索引时出错: {e}")
            self.use_faiss = False
            self.logger.warning("回退到sklearn进行向量检索")
        
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
        
        # 生成摘要的向量表示
        summary_embedding = self.embedding_model.encode(summary)
        self.summary_vectors[summary] = summary_embedding
        
        # 将向量添加到FAISS索引
        if self.use_faiss and self.index is not None:
            try:
                # 添加到摘要列表
                self.summaries_list.append(summary)
                
                # 准备向量数据，需要reshape为2D数组
                vector_np = np.array([summary_embedding], dtype=np.float32)
                
                # 添加到FAISS索引
                self.index.add(vector_np)
            except Exception as e:
                self.logger.error(f"将向量添加到FAISS索引时出错: {e}")
                
        return summary
    
    def batch_store(self, texts: List[str]) -> List[str]:
        """
        批量存储多个文本到RAG
        
        Args:
            texts: 需要存储的文本列表
            
        Returns:
            摘要列表
        """
        if not texts:
            return []
            
        summaries = []
        new_vectors = []
        new_summaries = []
        
        # 先生成所有摘要和向量
        for text in texts:
            summary = self.summarize_text(text)
            
            # 跳过重复项
            if summary in self.rag_store:
                summaries.append(summary)
                continue
                
            self.rag_store[summary] = text
            summary_embedding = self.embedding_model.encode(summary)
            self.summary_vectors[summary] = summary_embedding
            
            summaries.append(summary)
            new_vectors.append(summary_embedding)
            new_summaries.append(summary)
        
        # 如果使用FAISS，批量添加向量
        if self.use_faiss and self.index is not None and new_vectors:
            try:
                # 更新摘要列表
                self.summaries_list.extend(new_summaries)
                
                # 准备批量向量数据
                vectors_np = np.array(new_vectors, dtype=np.float32)
                
                # 批量添加到FAISS索引
                self.index.add(vectors_np)
                self.logger.info(f"已将{len(new_vectors)}个向量批量添加到FAISS索引")
            except Exception as e:
                self.logger.error(f"批量添加向量到FAISS索引时出错: {e}")
        
        return summaries
    
    def retrieve(self, query: str, top_k: int = 3) -> List[str]:
        """
        根据查询检索相关文本 (使用FAISS或向量相似度)
        
        Args:
            query: 查询文本
            top_k: 返回的最大结果数量
            
        Returns:
            检索到的文本列表
        """
        if not self.rag_store:
            return []
        
        # 如果向量存储为空，直接返回空列表
        if not self.summary_vectors:
            return []
            
        # 生成查询向量
        query_embedding = self.embedding_model.encode(query)
        
        # 使用FAISS进行检索
        if self.use_faiss and self.index is not None and len(self.summaries_list) > 0:
            try:
                # 准备查询向量
                query_vector = np.array([query_embedding], dtype=np.float32)
                
                # 执行搜索，返回距离和索引
                distances, indices = self.index.search(query_vector, min(top_k, len(self.summaries_list)))
                
                # 获取结果摘要，然后获取对应的原文本
                results = []
                for i, idx in enumerate(indices[0]):
                    if idx < len(self.summaries_list):
                        summary = self.summaries_list[idx]
                        # 检查距离是否在合理范围内（可选）
                        # 对于L2距离，较小的值表示更相似
                        # if distances[0][i] > max_distance:
                        #    continue
                        if summary in self.rag_store:
                            results.append(self.rag_store[summary])
                
                self.logger.debug(f"FAISS检索成功，找到{len(results)}个结果")
                return results
                
            except Exception as e:
                self.logger.error(f"使用FAISS检索时出错: {e}")
                self.logger.info("回退到sklearn进行向量检索")
                # 出错时回退到传统方法
        
        # 回退到传统的sklearn余弦相似度检索
        query_embedding = query_embedding.reshape(1, -1)
        
        # 准备摘要向量
        summaries = list(self.summary_vectors.keys())
        summary_embeddings = np.array([self.summary_vectors[s] for s in summaries])

        if summary_embeddings.ndim == 1: # 处理只有一个存储项的情况
            summary_embeddings = summary_embeddings.reshape(1, -1)
            
        # 计算余弦相似度
        similarities = cosine_similarity(query_embedding, summary_embeddings)[0]
        
        # 获取top_k索引
        top_k_indices = np.argsort(similarities)[::-1][:top_k]
        
        # 返回对应的原始文本，排除相似度小于或等于0的结果
        results = [self.rag_store[summaries[i]] for i in top_k_indices if similarities[i] > 0]
        
        self.logger.debug(f"sklearn检索成功，找到{len(results)}个结果")
        return results 