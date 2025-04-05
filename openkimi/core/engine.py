from typing import Dict, List, Any, Optional, Tuple
import os
import json
import logging

from openkimi.core.processor import TextProcessor
from openkimi.core.rag import RAGManager
from openkimi.core.framework import FrameworkGenerator
from openkimi.utils.llm_interface import LLMInterface, get_llm_interface, TokenCounter

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class KimiEngine:
    """OpenKimi主引擎：整合所有模块，提供具有递归RAG和MCP的长对话能力"""
    
    def __init__(self, 
                 config_path: Optional[str] = None, 
                 llm_config: Optional[Dict] = None,
                 processor_config: Optional[Dict] = None,
                 rag_config: Optional[Dict] = None,
                 mcp_candidates: int = 1 # Default to 1 (no MCP) for simplicity
                 ):
        """
        初始化Kimi引擎
        
        Args:
            config_path: 配置文件路径 (JSON)
            llm_config: LLM 配置字典 (覆盖配置文件)
            processor_config: 文本处理器配置字典 (覆盖配置文件)
            rag_config: RAG 配置字典 (覆盖配置文件)
            mcp_candidates: MCP候选方案数量 (1表示禁用MCP)
        """
        # 加载配置
        self.config = self._load_config(config_path)
        
        # Overwrite with specific configs if provided
        if llm_config: self.config['llm'] = {**self.config.get('llm', {}), **llm_config}
        if processor_config: self.config['processor'] = {**self.config.get('processor', {}), **processor_config}
        if rag_config: self.config['rag'] = {**self.config.get('rag', {}), **rag_config}
        
        self.mcp_candidates = mcp_candidates
        logger.info(f"Initializing KimiEngine with config: {self.config}")
        logger.info(f"MCP candidates: {self.mcp_candidates}")
                
        # 初始化LLM接口和 Tokenizer
        self.llm_interface = get_llm_interface(self.config["llm"])
        self.tokenizer = self.llm_interface.get_tokenizer()
        self.token_counter = TokenCounter(self.tokenizer)
        self.max_context_tokens = self.llm_interface.get_max_context_length() 
        # Reserve some tokens for generation and overhead
        self.max_prompt_tokens = int(self.max_context_tokens * 0.8) 
        logger.info(f"LLM Max Context Tokens: {self.max_context_tokens}, Max Prompt Tokens: {self.max_prompt_tokens}")

        # 初始化各个模块
        proc_cfg = self.config.get('processor', {})
        rag_cfg = self.config.get('rag', {})
        self.processor = TextProcessor(batch_size=proc_cfg.get('batch_size', 512))
        self.rag_manager = RAGManager(self.llm_interface, embedding_model_name=rag_cfg.get('embedding_model', 'all-MiniLM-L6-v2'))
        self.framework_generator = FrameworkGenerator(self.llm_interface) # FrameworkGenerator now also needs recursive logic potentially
        
        # 会话历史
        self.conversation_history: List[Dict[str, str]] = []
        
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """ Loads configuration from a JSON file, merging with defaults. """
        default_config = {
            "llm": {"type": "dummy"},
            "processor": {"batch_size": 512, "entropy_threshold": 3.0},
            "rag": {"embedding_model": "all-MiniLM-L6-v2", "top_k": 3},
            "mcp_candidates": 1 # Default to no MCP
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
                # Update mcp_candidates if present in the loaded config
                if "mcp_candidates" in config:
                     self.mcp_candidates = config["mcp_candidates"]
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
        temp_rag = RAGManager(self.llm_interface, embedding_model_name=self.config.get('rag', {}).get('embedding_model', 'all-MiniLM-L6-v2'))
        
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
        处理用户查询并生成回复 (with recursive RAG and optional MCP)
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
        
        # --- Solution Generation (with MCP) --- 
        logger.info(f"Generating solution using MCP (candidates={self.mcp_candidates})...")
        # Useful context for solution might be different, maybe more focused history + RAG
        solution_useful_context = context # For now, reuse the context from framework gen
        
        # Note: The framework generator methods themselves need internal _prepare_llm_input calls
        # This is currently missing in the framework.py implementation and needs adding there.
        # For now, we assume the framework generator handles its own prompt limits internally.
        
        solution = self.framework_generator.generate_solution_mcp(
            query, 
            framework, 
            useful_context=solution_useful_context, 
            rag_context=rag_context, # Pass retrieved snippets
            num_candidates=self.mcp_candidates
        )
        logger.info(f"Generated final solution: {solution[:100]}...")
        
        # 添加回复到会话历史
        self.conversation_history.append({"role": "assistant", "content": solution})
        
        return solution
    
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
        logger.info("Resetting KimiEngine state.")
        self.conversation_history = []
        # Reset RAG manager as well (clears stored summaries and vectors)
        rag_cfg = self.config.get('rag', {})
        self.rag_manager = RAGManager(self.llm_interface, embedding_model_name=rag_cfg.get('embedding_model', 'all-MiniLM-L6-v2')) 