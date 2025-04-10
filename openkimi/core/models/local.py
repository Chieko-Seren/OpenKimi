from typing import AsyncGenerator, Optional
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from accelerate import init_empty_weights, load_checkpoint_and_dispatch
from .base import BaseModel

class LocalModel(BaseModel):
    """支持量化和Accelerate的本地模型实现"""
    
    def __init__(
        self,
        model_path: str,
        device: str = "auto",
        load_in_8bit: bool = False,
        load_in_4bit: bool = False,
        use_flash_attention: bool = True,
        use_accelerate: bool = True
    ):
        """初始化本地模型
        
        Args:
            model_path: 模型路径或Hugging Face模型名称
            device: 运行设备 ("auto", "cpu", "cuda", "mps")
            load_in_8bit: 是否使用8位量化
            load_in_4bit: 是否使用4位量化
            use_flash_attention: 是否使用Flash Attention
            use_accelerate: 是否使用Accelerate进行模型加载
        """
        self.model_path = model_path
        self.device = self._get_device(device)
        
        # 配置量化参数
        quantization_config = None
        if load_in_8bit or load_in_4bit:
            quantization_config = BitsAndBytesConfig(
                load_in_8bit=load_in_8bit,
                load_in_4bit=load_in_4bit,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4"
            )
            
        # 加载tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_path,
            trust_remote_code=True
        )
        
        # 根据配置加载模型
        if use_accelerate:
            # 使用Accelerate加载模型
            with init_empty_weights():
                self.model = AutoModelForCausalLM.from_pretrained(
                    model_path,
                    trust_remote_code=True,
                    quantization_config=quantization_config,
                    use_flash_attention_2=use_flash_attention
                )
                
            # 使用Accelerate分发模型
            self.model = load_checkpoint_and_dispatch(
                self.model,
                model_path,
                device_map="auto",
                no_split_module_classes=["GPTNeoXLayer"]
            )
        else:
            # 常规加载方式
            self.model = AutoModelForCausalLM.from_pretrained(
                model_path,
                trust_remote_code=True,
                quantization_config=quantization_config,
                use_flash_attention_2=use_flash_attention,
                device_map="auto" if self.device == "cuda" else None
            )
            
            if self.device != "cuda":
                self.model = self.model.to(self.device)
                
        # 设置模型为评估模式
        self.model.eval()
        
    def _get_device(self, device: str) -> str:
        """确定运行设备"""
        if device == "auto":
            if torch.cuda.is_available():
                return "cuda"
            elif torch.backends.mps.is_available():
                return "mps"
            else:
                return "cpu"
        return device
        
    async def generate(self, prompt: str, max_tokens: Optional[int] = None) -> str:
        """生成文本"""
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_tokens if max_tokens else 512,
                do_sample=True,
                temperature=0.7,
                top_p=0.9,
                pad_token_id=self.tokenizer.eos_token_id
            )
            
        return self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
    async def stream_generate(self, prompt: str, max_tokens: Optional[int] = None) -> AsyncGenerator[str, None]:
        """流式生成文本"""
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        
        streamer = TextIteratorStreamer(self.tokenizer, skip_special_tokens=True)
        generation_kwargs = {
            **inputs,
            "max_new_tokens": max_tokens if max_tokens else 512,
            "do_sample": True,
            "temperature": 0.7,
            "top_p": 0.9,
            "pad_token_id": self.tokenizer.eos_token_id,
            "streamer": streamer
        }
        
        # 在后台线程中运行生成
        thread = Thread(target=self.model.generate, kwargs=generation_kwargs)
        thread.start()
        
        # 流式返回生成的文本
        for text in streamer:
            yield text
            
    @property
    def supports_streaming(self) -> bool:
        return True
        
    @property
    def max_context_length(self) -> int:
        # 从模型配置中获取最大上下文长度
        return self.model.config.max_position_embeddings 