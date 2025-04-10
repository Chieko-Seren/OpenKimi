from typing import Dict, List, Tuple, Any, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import logging
import traceback
import faiss
from .models.base import BaseModel

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
    """增强版RAG管理器，支持递归RAG和上下文长度检查"""
    
    def __init__(
        self,
        model: BaseModel,
        embedding_model_name: str = "all-MiniLM-L6-v2",
        use_faiss: bool = True,
        max_chunk_size: int = 512,
        overlap_size: int = 50,
        similarity_threshold: float = 0.7
    ):
        """初始化RAG管理器
        
        Args:
            model: 用于生成摘要的模型
            embedding_model_name: 用于生成embeddings的模型名称
            use_faiss: 是否使用FAISS进行向量检索
            max_chunk_size: 文本分块的最大大小
            overlap_size: 文本块之间的重叠大小
            similarity_threshold: 相似度阈值
        """
        self.logger = logging.getLogger(__name__)
        
        if model is None:
            self.logger.error("RAGManager初始化失败: model为None")
            raise ValueError("模型不能为None")
            
        self.model = model
        self.embedding_model = SentenceTransformer(embedding_model_name)
        self.use_faiss = use_faiss
        self.max_chunk_size = max_chunk_size
        self.overlap_size = overlap_size
        self.similarity_threshold = similarity_threshold
        
        # 初始化向量存储
        self.embeddings = []
        self.texts = []
        if use_faiss:
            self.index = faiss.IndexFlatL2(self.embedding_model.get_sentence_embedding_dimension())
        
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
        
    async def add_text(self, text: str) -> None:
        """添加文本到RAG存储
        
        Args:
            text: 要添加的文本
        """
        # 检查文本长度，如果超过模型的最大上下文长度，进行递归RAG
        if len(text.split()) > self.model.max_context_length:
            text = await self._recursive_rag_compress(text)
            
        # 分块处理文本
        chunks = self._split_text(text)
        
        # 为每个块生成摘要和embeddings
        for chunk in chunks:
            # 生成摘要
            summary = await self._generate_summary(chunk)
            
            # 生成embeddings
            embedding = self.embedding_model.encode([summary])[0]
            
            # 存储文本和embeddings
            self.texts.append(chunk)
            self.embeddings.append(embedding)
            
            if self.use_faiss:
                self.index.add(np.array([embedding], dtype=np.float32))
                
    async def search(self, query: str, top_k: int = 3) -> List[str]:
        """搜索相关文本
        
        Args:
            query: 搜索查询
            top_k: 返回的结果数量
            
        Returns:
            相关文本列表
        """
        # 生成查询的embedding
        query_embedding = self.embedding_model.encode([query])[0]
        
        if self.use_faiss:
            # 使用FAISS进行搜索
            distances, indices = self.index.search(
                np.array([query_embedding], dtype=np.float32),
                min(top_k, len(self.texts))
            )
            
            # 过滤掉相似度低于阈值的结果
            results = []
            for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
                if idx < len(self.texts):  # 确保索引有效
                    similarity = 1 / (1 + distance)  # 将距离转换为相似度
                    if similarity >= self.similarity_threshold:
                        results.append(self.texts[idx])
                        
            return results[:top_k]
        else:
            # 使用简单的余弦相似度搜索
            similarities = []
            for embedding in self.embeddings:
                similarity = np.dot(query_embedding, embedding) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(embedding)
                )
                similarities.append(similarity)
                
            # 获取top_k个最相似的结果
            top_indices = np.argsort(similarities)[-top_k:][::-1]
            return [self.texts[i] for i in top_indices if similarities[i] >= self.similarity_threshold]
            
    def _split_text(self, text: str) -> List[str]:
        """将文本分割成重叠的块"""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), self.max_chunk_size - self.overlap_size):
            chunk = " ".join(words[i:i + self.max_chunk_size])
            chunks.append(chunk)
            
        return chunks
        
    async def _generate_summary(self, text: str) -> str:
        """生成文本摘要"""
        prompt = f"""请为以下文本生成一个简洁的摘要，保留关键信息：

{text}

摘要："""
        
        return await this.model.generate(prompt)
        
    async def _recursive_rag_compress(self, text: str) -> str:
        """递归RAG压缩
        
        如果文本超过模型的最大上下文长度，递归地使用RAG进行压缩
        """
        # 分块处理文本
        chunks = self._split_text(text)
        
        # 为每个块生成摘要
        summaries = []
        for chunk in chunks:
            summary = await this._generate_summary(chunk)
            summaries.append(summary)
            
        # 合并摘要
        compressed_text = "\n\n".join(summaries)
        
        # 如果压缩后的文本仍然太长，递归压缩
        if len(compressed_text.split()) > this.model.max_context_length:
            return await this._recursive_rag_compress(compressed_text)
            
        return compressed_text
    
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
        summary = self.model.generate(prompt)
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
        if summary in self.texts: # Avoid duplicates, maybe update?
            return summary 
            
        self.texts.append(summary)
        
        # 生成摘要的向量表示
        summary_embedding = self.embedding_model.encode(summary)
        self.embeddings.append(summary_embedding)
        
        # 将向量添加到FAISS索引
        if self.use_faiss and self.index is not None:
            try:
                # 添加到摘要列表
                self.texts.append(summary)
                
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
            if summary in self.texts:
                summaries.append(summary)
                continue
                
            self.texts.append(summary)
            summary_embedding = self.embedding_model.encode(summary)
            self.embeddings.append(summary_embedding)
            
            summaries.append(summary)
            new_vectors.append(summary_embedding)
            new_summaries.append(summary)
        
        # 如果使用FAISS，批量添加向量
        if self.use_faiss and self.index is not None and new_vectors:
            try:
                # 更新摘要列表
                self.texts.extend(new_summaries)
                
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
        if not self.texts:
            return []
        
        # 如果向量存储为空，直接返回空列表
        if not self.embeddings:
            return []
            
        # 生成查询向量
        query_embedding = self.embedding_model.encode(query)
        
        # 使用FAISS进行检索
        if self.use_faiss and self.index is not None and len(self.texts) > 0:
            try:
                # 准备查询向量
                query_vector = np.array([query_embedding], dtype=np.float32)
                
                # 执行搜索，返回距离和索引
                distances, indices = self.index.search(query_vector, min(top_k, len(self.texts)))
                
                # 获取结果摘要，然后获取对应的原文本
                results = []
                for i, idx in enumerate(indices[0]):
                    if idx < len(self.texts):
                        summary = self.texts[idx]
                        # 检查距离是否在合理范围内（可选）
                        # 对于L2距离，较小的值表示更相似
                        # if distances[0][i] > max_distance:
                        #    continue
                        if summary in self.texts:
                            results.append(summary)
                
                self.logger.debug(f"FAISS检索成功，找到{len(results)}个结果")
                return results
                
            except Exception as e:
                self.logger.error(f"使用FAISS检索时出错: {e}")
                self.logger.info("回退到sklearn进行向量检索")
                # 出错时回退到传统方法
        
        # 回退到传统的sklearn余弦相似度检索
        query_embedding = query_embedding.reshape(1, -1)
        
        # 准备摘要向量
        summaries = self.texts
        summary_embeddings = np.array(self.embeddings)

        if summary_embeddings.ndim == 1: # 处理只有一个存储项的情况
            summary_embeddings = summary_embeddings.reshape(1, -1)
            
        # 计算余弦相似度
        similarities = cosine_similarity(query_embedding, summary_embeddings)[0]
        
        # 获取top_k索引
        top_k_indices = np.argsort(similarities)[::-1][:top_k]
        
        # 返回对应的原始文本，排除相似度小于或等于0的结果
        results = [self.texts[i] for i in top_k_indices if similarities[i] > 0]
        
        self.logger.debug(f"sklearn检索成功，找到{len(results)}个结果")
        return results 