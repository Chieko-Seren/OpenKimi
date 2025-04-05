from typing import Dict, List, Any, Optional
import os
import requests
from abc import ABC, abstractmethod
from dotenv import load_dotenv

# Load environment variables from .env file, if it exists
load_dotenv()

class LLMInterface(ABC):
    """LLM接口抽象类，用于与不同的大语言模型交互"""
    
    @abstractmethod
    def generate(self, prompt: str, max_new_tokens: int = 512, temperature: float = 0.7, **kwargs) -> str:
        """
        生成文本
        
        Args:
            prompt: 输入提示
            max_new_tokens: 最大生成 token 数
            temperature: 控制生成随机性
            **kwargs: 其他特定于实现的参数
            
        Returns:
            生成的文本
        """
        pass
        
    @abstractmethod
    def get_tokenizer(self):
        """获取与此 LLM 关联的 tokenizer。"""
        pass
        
    @abstractmethod
    def get_max_context_length(self) -> int:
        """获取模型的最大上下文长度（tokens）。"""
        pass

class DummyLLM(LLMInterface):
    """测试用的简单LLM实现"""
    def __init__(self):
        # Use a simple tokenizer for dummy length calculation
        print("初始化DummyLLM...")
        try:
            from transformers import AutoTokenizer
            # Use a common open-source model tokenizer like Llama's for approximation
            try:
                print("尝试加载hf-internal-testing/llama-tokenizer")
                self.tokenizer = AutoTokenizer.from_pretrained("hf-internal-testing/llama-tokenizer") 
                print("成功加载llama-tokenizer")
            except Exception as e:
                print(f"警告: 无法加载llama-tokenizer: {e}")
                print("尝试加载gpt2 tokenizer")
                try:
                    self.tokenizer = AutoTokenizer.from_pretrained("gpt2")
                    print("成功加载gpt2 tokenizer")
                except Exception as e2:
                    print(f"警告: 无法加载gpt2 tokenizer: {e2}")
                    print("使用内置简单分词器")
                    # 创建一个简单的分词器
                    self.tokenizer = SimpleTokenizer()
        except ImportError:
            print("警告: 无法导入transformers库，使用内置简单分词器")
            self.tokenizer = SimpleTokenizer()
            
        self.max_context = 2048 # Assume a common context length
        print("DummyLLM初始化完成")
        
    def generate(self, prompt: str, max_new_tokens: int = 50, temperature: float = 0.7, **kwargs) -> str:
        """
        简单的文本生成，仅用于测试
        """
        if "摘要" in prompt:
            return f"[Dummy Summary of: {prompt[:30]}...]"
        elif "框架" in prompt:
            return "[Dummy Framework: 1. Step A 2. Step B]"
        elif "候选方案" in prompt:
            return f"[Dummy Synthesized Solution for: {prompt[:30]}...]"
        else:
            return f"[Dummy Response to: {prompt[:30]}...]"
            
    def get_tokenizer(self):
        return self.tokenizer
        
    def get_max_context_length(self) -> int:
        return self.max_context
        
# 简单的内置分词器，用于fallback
class SimpleTokenizer:
    """极简的分词器，用于在无法加载transformers时使用"""
    def encode(self, text, max_length=None, truncation=False, **kwargs):
        # 简单地按字符分割
        tokens = list(text)
        if max_length and truncation and len(tokens) > max_length:
            tokens = tokens[:max_length]
        return tokens
    
    def decode(self, tokens):
        # 简单地拼接字符
        return ''.join(tokens)

class LocalLLM(LLMInterface):
    """本地LLM模型接口 (使用 Transformers)"""
    
    def __init__(self, model_path: str, device: str = 'auto'):
        """
        初始化本地LLM
        
        Args:
            model_path: 模型路径或Hugging Face Hub名称
            device: 推理设备 ('cpu', 'cuda', 'mps', 'auto')
        """
        from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer
        import torch
        
        self.model_path = model_path
        print(f"Loading local model: {model_path}...")
        
        # Determine device automatically if not specified
        if device == 'auto':
            if torch.cuda.is_available():
                self.device = 'cuda'
            elif torch.backends.mps.is_available(): # For Apple Silicon
                 self.device = 'mps'
            else:
                self.device = 'cpu'
        else:
            self.device = device
            
        # Todo: Add support for quantization (bitsandbytes)
        # Todo: Add support for accelerate for multi-GPU or large models
        try:
            # Try loading directly, assuming it fits in memory
            self.tokenizer = AutoTokenizer.from_pretrained(model_path)
            self.model = AutoModelForCausalLM.from_pretrained(model_path)
            # Try to move model to the selected device
            try:
                self.model.to(self.device)
                print(f"Model loaded on device: {self.device}")
            except Exception as e:
                print(f"Warning: Could not move model to {self.device}, using CPU. Error: {e}")
                self.device = 'cpu'
                self.model.to(self.device)
                
            # Create the pipeline after model is on the correct device
            self.pipeline = pipeline(
                'text-generation', 
                model=self.model, 
                tokenizer=self.tokenizer, 
                device=self.device if self.device != 'cpu' else -1 # pipeline uses -1 for cpu
            )
            self.max_context = self.model.config.max_position_embeddings if hasattr(self.model.config, 'max_position_embeddings') else 2048
            print(f"Model loaded successfully. Max context: {self.max_context}")

        except Exception as e:
            print(f"Error loading local model {model_path}: {e}")
            raise
        
    def generate(self, prompt: str, max_new_tokens: int = 512, temperature: float = 0.7, **kwargs) -> str:
        """
        使用本地模型生成文本
        """
        try:
            # Handle potential device placement issues if pipeline wasn't created properly
            if not hasattr(self, 'pipeline') or self.pipeline is None:
                 raise RuntimeError("Text generation pipeline not initialized correctly.")
                 
            # Some models might require specific kwargs, pass them along
            generation_kwargs = {
                "max_new_tokens": max_new_tokens,
                "temperature": temperature if temperature > 0 else None, # Temp 0 can cause issues
                "do_sample": temperature > 0, # Only sample if temperature > 0
                "pad_token_id": self.tokenizer.eos_token_id, # Avoid padding warning
                **kwargs
            }
            # Filter out None values from kwargs
            generation_kwargs = {k: v for k, v in generation_kwargs.items() if v is not None}
            
            # Ensure prompt isn't too long (basic check, more robust check in engine)
            # input_tokens = self.tokenizer(prompt, return_tensors="pt")['input_ids'].shape[1]
            # if input_tokens >= self.get_max_context_length():
            #    print(f"Warning: Prompt length ({input_tokens}) exceeds model max context ({self.get_max_context_length()}). May truncate or error.")

            results = self.pipeline(prompt, **generation_kwargs)
            if results and isinstance(results, list):
                generated_text = results[0]['generated_text']
                # Remove the original prompt from the generated text
                if generated_text.startswith(prompt):
                    return generated_text[len(prompt):].strip()
                else:
                    # Sometimes the prompt isn't perfectly included, handle simple cases
                    # This might need more robust handling depending on the model
                    print("Warning: Generated text didn't start with prompt as expected.")
                    return generated_text.strip() 
            return "" # Return empty if generation failed
        except Exception as e:
            print(f"Error during text generation with local model: {e}")
            # Provide more context if possible
            import traceback
            traceback.print_exc()
            return "[Error generating response]"
            
    def get_tokenizer(self):
        return self.tokenizer
        
    def get_max_context_length(self) -> int:
        return self.max_context

class APIBasedLLM(LLMInterface):
    """基于API的LLM接口 (OpenAI Compatible)"""
    
    def __init__(self, api_key: str = None, api_url: str = None, model_name: str = "gpt-3.5-turbo", context_length: int = 4096):
        """
        初始化API
        
        Args:
            api_key: API密钥 (reads from OPENAI_API_KEY env var if None)
            api_url: API地址 (reads from OPENAI_API_BASE env var if None, defaults to OpenAI)
            model_name: 要使用的模型名称
            context_length: 模型的上下文长度 (重要，因为API本身不一定提供)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.api_url = api_url or os.getenv("OPENAI_API_BASE") or "https://api.openai.com/v1/chat/completions"
        self.model_name = model_name
        self.max_context = context_length
        
        if not self.api_key:
            raise ValueError("API key not provided and OPENAI_API_KEY environment variable not set.")
            
        # Use a tokenizer compatible with the API model (e.g., GPT-4 tokenizer for OpenAI)
        # tiktoken is OpenAI's official one, but transformers is more general
        from transformers import AutoTokenizer
        try:
            # Try guessing tokenizer based on model name (might need adjustment)
            if "gpt-4" in model_name:
                 tokenizer_name = "openai-gpt" # Placeholder, tiktoken is better here
            elif "gpt-3.5" in model_name:
                 tokenizer_name = "gpt2" # Closer approximation
            else:
                 tokenizer_name = "gpt2" # Default fallback
            print(f"Using tokenizer approximation '{tokenizer_name}' for API model '{self.model_name}'")
            self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_name) 
        except Exception as e:
             print(f"Warning: Failed to load tokenizer {tokenizer_name}. Using gpt2 fallback. Error: {e}")
             self.tokenizer = AutoTokenizer.from_pretrained("gpt2")

    def generate(self, prompt: str, max_new_tokens: int = 512, temperature: float = 0.7, **kwargs) -> str:
        """
        通过API生成文本 (using Chat Completion endpoint)
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Use Chat Completion format
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_new_tokens,
            "temperature": temperature,
            **kwargs # Pass other compatible params like top_p, stop etc.
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=payload)
            response.raise_for_status()  # Raise an exception for bad status codes
            
            result = response.json()
            if result.get("choices") and len(result["choices"]) > 0:
                # Get content from the first choice's message
                message_content = result["choices"][0].get("message", {}).get("content")
                if message_content:
                    return message_content.strip()
                else:
                     print(f"Warning: API response structure unexpected or message content missing. Response: {result}")
                     return "[API response format error]"
            else:
                print(f"Warning: API response did not contain expected choices. Response: {result}")
                return "[API generation failed]"
                
        except requests.exceptions.RequestException as e:
            print(f"Error calling LLM API at {self.api_url}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                 print(f"Response status: {e.response.status_code}")
                 try:
                     print(f"Response body: {e.response.json()}")
                 except ValueError:
                     print(f"Response body: {e.response.text}")
            return "[API request error]"
        except Exception as e:
            print(f"An unexpected error occurred during API call: {e}")
            return "[Unexpected API error]"
            
    def get_tokenizer(self):
        return self.tokenizer
        
    def get_max_context_length(self) -> int:
        return self.max_context


def get_llm_interface(config: Dict[str, Any]) -> LLMInterface:
    """
    工厂函数，根据配置创建LLM接口
    
    Args:
        config: 配置字典, e.g., 
                {"type": "local", "model_path": "gpt2", "device": "cuda"}
                {"type": "api", "model_name": "gpt-4", "api_key": "sk-...", "context_length": 8192}
                {"type": "dummy"}
        
    Returns:
        LLM接口实例
    """
    llm_type = config.get("type", "dummy")
    print(f"Creating LLM interface of type: {llm_type}")
    
    if llm_type == "dummy":
        return DummyLLM()
    elif llm_type == "local":
        model_path = config.get("model_path")
        if not model_path:
            raise ValueError("本地LLM需要提供model_path")
        return LocalLLM(model_path, config.get("device", "auto"))
    elif llm_type == "api":
        return APIBasedLLM(
            api_key=config.get("api_key"), 
            api_url=config.get("api_url"), 
            model_name=config.get("model_name", "gpt-3.5-turbo"),
            context_length=config.get("context_length", 4096) # Default context length for API models
        )
    else:
        raise ValueError(f"不支持的LLM类型: {llm_type}")
        
# Simple Token Counter (can be refined)
class TokenCounter:
    def __init__(self, tokenizer):
        self.tokenizer = tokenizer
        
    def count_tokens(self, text: str) -> int:
        if not text: return 0
        # Use encode which is generally faster for just counting
        return len(self.tokenizer.encode(text)) 