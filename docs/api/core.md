# 核心模块 API 参考

本页详细介绍 `openkimi.core` 模块中的类和方法。

## KimiEngine

主引擎类，协调所有模块。

```python
class KimiEngine:
    def __init__(self, 
                 config_path: Optional[str] = None, 
                 llm_config: Optional[Dict] = None,
                 processor_config: Optional[Dict] = None,
                 rag_config: Optional[Dict] = None,
                 mpr_candidates: int = 1, 
                 session_id: Optional[str] = None):
        pass
        
    async def ingest(self, text: str) -> None:
        pass
        
    async def chat(self, query: str) -> str:
        pass
        
    async def stream_chat(self, query: str) -> AsyncGenerator[str, None]:
        pass
        
    def reset(self) -> None:
        pass
```

- `__init__`: 初始化引擎，参数与[配置指南](../guides/configuration.md)一致。
- `ingest`: 异步方法，摄入和处理长文本。
- `chat`: 异步方法，处理用户查询并返回完整回复。
- `stream_chat`: 异步生成器，流式处理用户查询并返回回复片段。
- `reset`: 重置会话历史和RAG存储。

## TextProcessor

文本处理器类。

```python
class TextProcessor:
    def __init__(self,
                 batch_size: int = 512,
                 entropy_threshold: float = 2.5,
                 overlap_size: int = 50,
                 entropy_method: str = "weighted"):
        pass
        
    def split_into_batches(self, text: str, by_sentence: bool = True) -> List[str]:
        pass
        
    def calculate_entropy(self, text: str, context_texts: Optional[List[str]] = None) -> Dict[str, float]:
        pass
        
    def classify_by_entropy(self, batches: List[str], 
                            threshold: Optional[float] = None,
                            context_aware: bool = True) -> Tuple[List[str], List[str]]:
        pass
        
    def get_batch_entropy_ranking(self, batches: List[str], 
                                  context_aware: bool = True) -> List[Tuple[str, float]]:
        pass
        
    def extract_key_segments(self, text: str, top_k: int = 3) -> List[str]:
        pass
```

- `__init__`: 初始化处理器，参数与[配置指南](../guides/configuration.md)一致。
- `split_into_batches`: 将文本分割成批次，可选按句子边界分割。
- `calculate_entropy`: 计算文本的信息熵，返回包含各种熵值的字典。
- `classify_by_entropy`: 根据信息熵对文本块进行分类。
- `get_batch_entropy_ranking`: 获取文本块的熵值排名。
- `extract_key_segments`: 提取文本中信息熵最高的片段。

## RAGManager

RAG（检索增强生成）管理器。

```python
class RAGManager:
    def __init__(self,
                 model: BaseModel,
                 embedding_model_name: str = "all-MiniLM-L6-v2",
                 use_faiss: bool = True,
                 max_chunk_size: int = 512,
                 overlap_size: int = 50,
                 similarity_threshold: float = 0.7):
        pass
        
    async def add_text(self, text: str) -> None:
        pass
        
    async def search(self, query: str, top_k: int = 3) -> List[str]:
        pass
        
    async def batch_store(self, texts: List[str]) -> List[str]:
        pass
        
    async def retrieve(self, query: str, top_k: int = 3) -> List[str]:
        pass
        
    async def _recursive_rag_compress(self, text: str) -> str:
        pass
```

- `__init__`: 初始化RAG管理器，参数与[配置指南](../guides/configuration.md)一致。
- `add_text`: 异步方法，添加文本到RAG存储。
- `search`: 异步方法，搜索相关文本。
- `batch_store`: 异步方法，批量存储文本。
- `retrieve`: 异步方法，检索与查询最相关的文本。
- `_recursive_rag_compress`: 异步方法，执行递归RAG压缩（内部使用）。

## FrameworkGenerator

解决方案框架生成器。

```python
class FrameworkGenerator:
    def __init__(self, model: BaseModel):
        pass
        
    async def generate_framework(self, query: str, context: str) -> str:
        pass
        
    async def generate_solution_mpr(self,
                                      query: str,
                                      framework: str,
                                      useful_context: str,
                                      rag_context: List[str],
                                      num_candidates: int = 3,
                                      context_strategy: str = "diversity",
                                      synthesis_strategy: str = "hierarchical") -> str:
        pass
```

- `__init__`: 初始化框架生成器。
- `generate_framework`: 异步方法，生成解决方案框架。
- `generate_solution_mpr`: 异步方法，使用MPR策略生成最终解决方案。参数详细说明见[MPR指南](../guides/mpr.md)。

## EntropyEvaluator

信息熵评估器。

```python
class EntropyEvaluator:
    def __init__(self,
                 use_tfidf: bool = True,
                 ngram_range: tuple = (1, 2),
                 max_features: int = 10000):
        pass
        
    def calculate_word_entropy(self, text: str) -> float:
        pass
        
    def calculate_ngram_entropy(self, text: str, n: int = 2) -> float:
        pass
        
    def calculate_semantic_entropy(self, texts: List[str]) -> float:
        pass
        
    def calculate_structural_entropy(self, text: str) -> float:
        pass
        
    def evaluate_text(self,
                        text: str,
                        texts: Optional[List[str]] = None,
                        weights: Optional[Dict[str, float]] = None) -> Dict[str, float]:
        pass
```

- `__init__`: 初始化熵评估器。
- `calculate_word_entropy`: 计算词级别的信息熵。
- `calculate_ngram_entropy`: 计算n-gram级别的信息熵。
- `calculate_semantic_entropy`: 计算语义级别的信息熵。
- `calculate_structural_entropy`: 计算结构级别的信息熵。
- `evaluate_text`: 综合评估文本的信息熵，返回包含各种熵值的字典。 