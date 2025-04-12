from typing import Dict, List, Any, Optional, Tuple
import os
import json
import logging
import asyncio
import uuid

from openkimi.core.processor import TextProcessor
from openkimi.core.rag import RAGManager
from openkimi.core.framework import FrameworkGenerator
from openkimi.utils.llm_interface import LLMInterface, get_llm_interface, TokenCounter

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class KimiEngine:
    """OpenKimi主引擎：整合所有模块，提供具有递归RAG和MPR的长对话能力"""
    
    def __init__(self, 
                 config_path: Optional[str] = None, 
                 llm_config: Optional[Dict] = None,
                 processor_config: Optional[Dict] = None,
                 rag_config: Optional[Dict] = None,
                 mpr_candidates: int = 1, # Default to 1 (no MPR) for simplicity
                 session_id: Optional[str] = None # 添加会话ID支持
                 ):
        """
        初始化OpenKimi引擎
        
        Args:
            config_path: 配置文件路径，可选
            llm_config: LLM配置字典，可选，覆盖配置文件中的LLM配置
            processor_config: 处理器配置字典，可选，覆盖配置文件中的处理器配置
            rag_config: RAG配置字典，可选，覆盖配置文件中的RAG配置
            mpr_candidates: MPR候选数量，默认为1（禁用MPR）
            session_id: 会话ID，可选，用于追踪多个会话
        """
        self.logger = logging.getLogger(__name__)
        
        # 加载配置
        self.config = self._load_config(config_path)
        
        # 覆盖配置文件中的设置（如果提供了参数）
        if llm_config:
            self.config["llm"] = llm_config
        if processor_config:
            self.config["processor"] = processor_config
        if rag_config:
            self.config["rag"] = rag_config
            
        # MPR候选数量（命令行参数优先）
        self.mpr_candidates = mpr_candidates
        # 如果命令行没指定，但配置文件中有，则使用配置文件的值
        if mpr_candidates == 1 and "mpr_candidates" in self.config:
            self.mpr_candidates = self.config["mpr_candidates"]
            
        # 会话ID
        self.session_id = session_id or str(uuid.uuid4())
        
        logger.info(f"Initializing KimiEngine with config: {self.config}")
        logger.info(f"MPR candidates: {self.mpr_candidates}")
        if session_id:
            logger.info(f"Session ID: {session_id}")
                
        # 初始化LLM接口和 Tokenizer
        try:
            logger.info("开始初始化LLM接口...")
            from openkimi.utils.llm_interface import get_llm_interface
            self.llm_interface = get_llm_interface(self.config["llm"])
            if self.llm_interface is None:
                logger.error("LLM接口初始化返回了None")
                raise RuntimeError("LLM接口初始化失败")
                
            self.tokenizer = self.llm_interface.get_tokenizer()
            self.token_counter = TokenCounter(self.tokenizer)
            self.max_context_tokens = self.llm_interface.get_max_context_length() 
            # Reserve some tokens for generation and overhead
            self.max_prompt_tokens = int(self.max_context_tokens * 0.8) 
            logger.info(f"LLM Max Context Tokens: {self.max_context_tokens}, Max Prompt Tokens: {self.max_prompt_tokens}")
        except Exception as e:
            logger.error(f"初始化LLM接口时出错: {e}")
            import traceback
            traceback.print_exc()
            raise RuntimeError(f"LLM接口初始化失败: {e}")

        # 初始化各个模块
        try:
            proc_cfg = self.config.get('processor', {})
            rag_cfg = self.config.get('rag', {})
            self.processor = TextProcessor(batch_size=proc_cfg.get('batch_size', 512))
            
            try:
                logger.info(f"初始化RAGManager，配置: {rag_cfg}")
                self.rag_manager = RAGManager(
                    self.llm_interface, 
                    embedding_model_name=rag_cfg.get('embedding_model', 'all-MiniLM-L6-v2'),
                    use_faiss=rag_cfg.get('use_faiss', True)
                )
            except Exception as rag_error:
                logger.error(f"初始化RAGManager时出错: {rag_error}")
                import traceback
                traceback.print_exc()
                raise RuntimeError(f"RAG初始化失败: {rag_error}")
                
            self.framework_generator = FrameworkGenerator(self.llm_interface) # FrameworkGenerator now also needs recursive logic potentially
        except Exception as e:
            logger.error(f"初始化模块时出错: {e}")
            import traceback
            traceback.print_exc()
            raise RuntimeError(f"模块初始化失败: {e}")
        
        # 会话历史
        self.conversation_history: List[Dict[str, str]] = []
        logger.info("KimiEngine初始化完成")
        
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """ Loads configuration from a JSON file, merging with defaults. """
        default_config = {
            "llm": {"type": "dummy"},
            "processor": {"batch_size": 512, "entropy_threshold": 3.0},
            "rag": {"embedding_model": "all-MiniLM-L6-v2", "top_k": 3, "use_faiss": True},
            "mpr_candidates": 1 # Default to no MPR
        }
        
        if not config_path:
            logger.warning("No config path provided, using default config.")
            return default_config
            
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                logger.info(f"Loaded config from {config_path}")
                # Deep merge with defaults (simple version)
                merged_config = default_config.copy()
                for key, value in config.items():
                    if key in merged_config and isinstance(merged_config[key], dict) and isinstance(value, dict):
                        merged_config[key].update(value)
                    else:
                        merged_config[key] = value
                # Update mpr_candidates if present in the loaded config
                if "mpr_candidates" in config:
                     self.mpr_candidates = config["mpr_candidates"]
                     
                # 向后兼容：如果配置中有mcp_candidates，但没有mpr_candidates
                if "mcp_candidates" in config and "mpr_candidates" not in config:
                     self.mpr_candidates = config["mcp_candidates"]
                     
                return merged_config
        except FileNotFoundError:
            logger.warning(f"Config file not found at {config_path}, using default config.")
            return default_config
        except json.JSONDecodeError:
             logger.error(f"Error decoding JSON from config file: {config_path}. Using default config.")
             return default_config
        except Exception as e:
            logger.error(f"Error loading config file {config_path}: {e}. Using default config.")
            return default_config
            
    def _recursive_rag_compress(self, text: str, target_token_limit: int) -> str:
        """ Recursively compresses text using RAG until it fits the token limit. """
        current_tokens = self.token_counter.count_tokens(text)
        logger.debug(f"_recursive_rag_compress called. Current tokens: {current_tokens}, Target limit: {target_token_limit}")
        
        if current_tokens <= target_token_limit:
            logger.debug("Text already within limit.")
            return text

        logger.info(f"Text exceeds limit ({current_tokens} > {target_token_limit}). Compressing...")
        # Use a temporary RAG store for this compression cycle
        rag_cfg = self.config.get('rag', {})
        temp_rag = RAGManager(
            self.llm_interface, 
            embedding_model_name=rag_cfg.get('embedding_model', 'all-MiniLM-L6-v2'),
            use_faiss=rag_cfg.get('use_faiss', True)
        )
        
        # Split, classify, and store less useful parts
        batches = self.processor.split_into_batches(text)
        useful_batches, less_useful_batches = self.processor.classify_by_entropy(
            batches, threshold=self.config['processor'].get('entropy_threshold', 3.0)
        )
        temp_rag.batch_store(less_useful_batches)
        
        # Keep useful parts + summaries of less useful parts (represented by keys)
        compressed_text_parts = useful_batches + list(temp_rag.rag_store.keys())
        compressed_text = "\n".join(compressed_text_parts) # Join useful text and summaries
        new_tokens = self.token_counter.count_tokens(compressed_text)
        
        logger.info(f"Compression reduced tokens from {current_tokens} to {new_tokens}")
        
        # Recursively call if still too long
        if new_tokens > target_token_limit:
            logger.warning(f"Compressed text still too long ({new_tokens} > {target_token_limit}). Repeating compression.")
            # We might need a safety break here to prevent infinite loops
            if len(compressed_text) < len(text) * 0.9: # Basic check if significant reduction happened
                 return self._recursive_rag_compress(compressed_text, target_token_limit)
            else:
                 logger.error("Compression failed to significantly reduce size. Truncating.")
                 # Fallback: Truncate (should be smarter, e.g., truncate middle/end)
                 encoded = self.tokenizer.encode(compressed_text, max_length=target_token_limit, truncation=True)
                 return self.tokenizer.decode(encoded)
        else:
            return compressed_text
            
    def _prepare_llm_input(self, prompt: str) -> str:
        """ Ensures the prompt fits within the model's limit using recursive RAG. """
        prompt_tokens = self.token_counter.count_tokens(prompt)
        if prompt_tokens <= self.max_prompt_tokens:
            return prompt
        else:
            logger.info(f"Prompt too long ({prompt_tokens} tokens > {self.max_prompt_tokens}). Applying RAG compression.")
            return self._recursive_rag_compress(prompt, self.max_prompt_tokens)

    def ingest(self, text: str) -> None:
        """
        摄入文本，进行预处理和RAG存储 (handles potential long input)
        """
        logger.info(f"Ingesting text of length {len(text)} characters.")
        # Check if the initial text itself needs compression before even batching for main RAG
        ingest_text = self._prepare_llm_input(text) # Use max_prompt_tokens as a general limit for manageable chunks
        
        # Text分块
        batches = self.processor.split_into_batches(ingest_text)
        
        # 基于信息熵分类
        useful_batches, less_useful_batches = self.processor.classify_by_entropy(
            batches, 
            threshold=self.config["processor"].get("entropy_threshold", 3.0)
        )
        
        # 将低信息熵文本存入主 RAG
        stored_summaries = self.rag_manager.batch_store(less_useful_batches)
        logger.info(f"Stored {len(stored_summaries)} items in RAG.")
        
        # 将有用文本添加到会话历史 (or potentially a separate document store)
        useful_content = "\n".join(useful_batches)
        self.conversation_history.append({
            "role": "system", # Or maybe 'document'?
            "content": useful_content
        })
        logger.info(f"Added {len(useful_batches)} useful batches to context.")
        
    def chat(self, query: str) -> str:
        """
        处理用户查询并生成回复 (with recursive RAG and optional MPR)
        """
        logger.info(f"Received chat query: '{query[:50]}...'")
        # 添加用户查询到会话历史
        self.conversation_history.append({"role": "user", "content": query})
        
        # 从主 RAG 检索相关信息
        rag_top_k = self.config.get('rag', {}).get('top_k', 3)
        rag_context = self.rag_manager.retrieve(query, top_k=rag_top_k)
        logger.info(f"Retrieved {len(rag_context)} relevant context(s) from RAG.")
        
        # 获取最近的会话内容作为上下文 (fitting within limits)
        context = self._get_recent_context(self.max_prompt_tokens // 2) # Allocate roughly half for history
        logger.debug(f"Recent context length: {self.token_counter.count_tokens(context)} tokens")
        
        # --- Framework Generation --- 
        # Prepare context for framework generation (might include history)
        framework_input_context = context # Or potentially add retrieved RAG snippets here too?
        framework_input_context_prepared = self._prepare_llm_input(framework_input_context)
        logger.info("Generating solution framework...")
        framework = self.framework_generator.generate_framework(query, framework_input_context_prepared)
        logger.info(f"Generated framework: {framework[:100]}...")
        
        # --- Solution Generation (with MPR) --- 
        logger.info(f"Generating solution using MPR (candidates={self.mpr_candidates})...")
        # Useful context for solution might be different, maybe more focused history + RAG
        solution_useful_context = context # For now, reuse the context from framework gen
        
        # Note: The framework generator methods themselves need internal _prepare_llm_input calls
        # This is currently missing in the framework.py implementation and needs adding there.
        # For now, we assume the framework generator handles its own prompt limits internally.
        
        solution = self.framework_generator.generate_solution_mpr(
            query, 
            framework, 
            useful_context=solution_useful_context, 
            rag_context=rag_context, # Pass retrieved snippets
            num_candidates=self.mpr_candidates
        )
        logger.info(f"Generated final solution: {solution[:100]}...")
        
        # 添加回复到会话历史
        self.conversation_history.append({"role": "assistant", "content": solution})
        
        return solution
    
    async def stream_chat(self, query: str) -> AsyncGenerator[str, None]:
        """
        流式处理用户查询并生成回复 (支持异步生成和流式输出)
        
        Args:
            query: 用户查询
            
        Yields:
            生成的回复片段
        """
        logger.info(f"Received stream chat query: '{query[:50]}...'")
        
        # 添加用户查询到会话历史
        self.conversation_history.append({"role": "user", "content": query})
        
        # 从主 RAG 检索相关信息
        rag_top_k = self.config.get('rag', {}).get('top_k', 3)
        rag_context = self.rag_manager.retrieve(query, top_k=rag_top_k)
        logger.info(f"Retrieved {len(rag_context)} relevant context(s) from RAG.")
        
        # 获取最近的会话内容作为上下文 (fitting within limits)
        context = self._get_recent_context(self.max_prompt_tokens // 2) # Allocate roughly half for history
        logger.debug(f"Recent context length: {self.token_counter.count_tokens(context)} tokens")
        
        # 生成解决方案框架
        framework_input_context = context
        framework_input_context_prepared = self._prepare_llm_input(framework_input_context)
        logger.info("Generating solution framework...")
        framework = self.framework_generator.generate_framework(query, framework_input_context_prepared)
        logger.info(f"Generated framework: {framework[:100]}...")
        
        # 准备生成解决方案的上下文
        solution_useful_context = context
        
        # 检查LLM接口是否支持流式生成
        if hasattr(self.llm_interface, 'stream_generate') and callable(self.llm_interface.stream_generate):
            # 使用LLM接口的流式生成功能
            full_response = ""
            async for chunk in self.llm_interface.stream_generate(
                query, 
                context=solution_useful_context,
                framework=framework,
                rag_context=rag_context
            ):
                full_response += chunk
                yield chunk
                
            # 添加完整回复到会话历史
            self.conversation_history.append({"role": "assistant", "content": full_response})
        else:
            # 如果不支持流式生成，则使用普通chat并模拟流式输出
            solution = self.framework_generator.generate_solution_mpr(
                query, 
                framework, 
                useful_context=solution_useful_context, 
                rag_context=rag_context,
                num_candidates=self.mpr_candidates
            )
            
            # 模拟流式输出，每10个字符发送一次
            for i in range(0, len(solution), 10):
                chunk = solution[i:i+10]
                yield chunk
                await asyncio.sleep(0.05)  # 添加小延迟以模拟流式输出
                
            # 添加完整回复到会话历史
            self.conversation_history.append({"role": "assistant", "content": solution})
        
    def _get_recent_context(self, max_tokens: int) -> str:
        """ Gets recent conversation history, ensuring it fits max_tokens. """
        recent_messages_text = []
        current_tokens = 0
        
        # Iterate in reverse (most recent first)
        for message in reversed(self.conversation_history):
            msg_text = f"{message['role']}: {message['content']}"
            msg_tokens = self.token_counter.count_tokens(msg_text)
            
            # Check if adding this message exceeds the limit
            if current_tokens + msg_tokens > max_tokens:
                # If even the first message is too long, truncate it
                if not recent_messages_text:
                     logger.warning(f"Single message exceeds max_tokens ({msg_tokens} > {max_tokens}). Truncating message.")
                     encoded = self.tokenizer.encode(msg_text, max_length=max_tokens, truncation=True)
                     recent_messages_text.append(self.tokenizer.decode(encoded))
                     current_tokens = max_tokens # Set to max as we truncated
                break # Stop adding messages
                
            recent_messages_text.append(msg_text)
            current_tokens += msg_tokens
            
        # Return in chronological order
        final_context = "\n\n".join(reversed(recent_messages_text))
        logger.debug(f"_get_recent_context: Final tokens: {self.token_counter.count_tokens(final_context)}")
        return final_context
    
    def reset(self) -> None:
        """重置会话历史和 RAG 存储"""
        logger.info(f"Resetting KimiEngine state. Session ID: {self.session_id}")
        self.conversation_history = []
        # Reset RAG manager as well (clears stored summaries and vectors)
        rag_cfg = self.config.get('rag', {})
        # 确保llm_interface不会为None
        if self.llm_interface is not None:
            try:
                logger.info(f"重新初始化RAGManager，配置: {rag_cfg}")
                self.rag_manager = RAGManager(
                    self.llm_interface, 
                    embedding_model_name=rag_cfg.get('embedding_model', 'all-MiniLM-L6-v2'),
                    use_faiss=rag_cfg.get('use_faiss', True)
                )
                logger.info("RAGManager重置成功")
            except Exception as e:
                logger.error(f"重置RAGManager时出错: {e}")
                import traceback
                traceback.print_exc()
                raise RuntimeError(f"RAG重置失败: {e}")
        else:
            logger.error("Cannot reset RAG manager: llm_interface is None")
            # 重新创建llm_interface
            try:
                from openkimi.utils.llm_interface import get_llm_interface
                logger.info(f"尝试重新初始化LLM接口，配置: {self.config['llm']}")
                self.llm_interface = get_llm_interface(self.config["llm"])
                if self.llm_interface is not None:
                    logger.info("LLM接口重新初始化成功")
                    try:
                        self.rag_manager = RAGManager(
                            self.llm_interface, 
                            embedding_model_name=rag_cfg.get('embedding_model', 'all-MiniLM-L6-v2'),
                            use_faiss=rag_cfg.get('use_faiss', True)
                        )
                        logger.info("RAGManager重置成功")
                    except Exception as e:
                        logger.error(f"重置RAGManager时出错: {e}")
                        import traceback
                        traceback.print_exc()
                        raise RuntimeError(f"RAG重置失败: {e}")
                else:
                    logger.critical("Failed to recreate llm_interface during reset")
                    raise RuntimeError("LLM接口重新初始化失败")
            except Exception as e:
                logger.critical(f"重新初始化LLM接口时出错: {e}")
                import traceback
                traceback.print_exc()
                raise RuntimeError(f"LLM接口重新初始化失败: {e}")
                
    def get_session_id(self) -> Optional[str]:
        """获取会话ID"""
        return self.session_id
        
    def set_session_id(self, session_id: str) -> None:
        """设置会话ID"""
        self.session_id = session_id
        logger.info(f"设置会话ID: {session_id}") 