import time
import uuid
import os
import argparse
import sys
import logging
import shutil
from typing import Optional, List
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse, JSONResponse # Add JSONResponse
from fastapi.middleware.cors import CORSMiddleware  # 导入CORS中间件
import uvicorn
import requests # Import requests
import json # Import json

# Setup logging
logger = logging.getLogger(__name__)

# Add project root to sys.path to allow importing openkimi
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from openkimi import KimiEngine
from openkimi.utils.llm_interface import get_llm_interface
from openkimi.api.models import ChatCompletionRequest, ChatCompletionResponse, ChatMessage, ChatCompletionChoice, CompletionUsage

app = FastAPI(
    title="OpenKimi API",
    description="OpenAI-compatible API for the OpenKimi long context engine.",
    version="0.1.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源，生产环境中应限制为特定来源
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有方法
    allow_headers=["*"],  # 允许所有头部
)

# Global variable to hold the KimiEngine instance
# This is simple; for production, consider dependency injection frameworks
engine: Optional[KimiEngine] = None
engine_model_name: str = "openkimi-engine"

# 文件上传存储目录
UPLOAD_DIR = os.path.join(project_root, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 存储已上传文件的信息
uploaded_files = {}

def initialize_engine(args):
    """Initializes the global KimiEngine based on args."""
    global engine, engine_model_name
    print("Initializing Kimi Engine for API server...")
    
    if not args.config or not os.path.exists(args.config):
        print(f"ERROR: 配置文件不存在: {args.config}")
        engine = None
        return
        
    try:
        print(f"正在使用配置文件: {args.config}")
        with open(args.config, 'r') as f:
            config_content = f.read()
            print(f"配置文件内容: {config_content}")
        
        # 尝试验证JSON格式    
        try:
            json_config = json.loads(config_content)
            print(f"JSON解析成功: {json_config}")
        except json.JSONDecodeError as e:
            print(f"JSON解析失败: {e}")
            
        # 检查transformers库是否正确安装 (DummyLLM需要)
        try:
            import transformers
            print(f"Transformers库版本: {transformers.__version__}")
        except ImportError:
            print("错误: Transformers库未安装或无法导入")
            print("请运行: pip install transformers")
            engine = None
            return
            
        # 检查sentence-transformers库是否正确安装 (RAG需要)
        try:
            import sentence_transformers
            print(f"Sentence-Transformers库版本: {sentence_transformers.__version__}")
        except ImportError:
            print("错误: sentence-transformers库未安装或无法导入")
            print("请运行: pip install sentence-transformers")
            engine = None
            return
                
        print("开始初始化KimiEngine实例...")
        engine = KimiEngine(
            config_path=args.config,
            # You might want to load LLM/processor/RAG configs directly here too
            # based on args if needed, e.g.:
            # llm_config={"model_path": args.model} if args.model else None,
            mcp_candidates=args.mcp_candidates
        )
        # Try to get a more descriptive model name if possible from config
        engine_model_name = engine.config.get("llm", {}).get("model_name") or \
                            engine.config.get("llm", {}).get("model_path") or \
                            f"openkimi-{engine.config.get('llm', {}).get('type', 'unknown')}"
        print(f"Kimi Engine initialized successfully. Using model identifier: {engine_model_name}")
        
        # 验证engine和llm_interface是否正确初始化
        if engine.llm_interface is None:
            print("WARNING: engine.llm_interface is None after initialization!")
            # 尝试重新初始化llm_interface
            print(f"尝试重新初始化LLM接口，配置: {engine.config['llm']}")
            try:
                engine.llm_interface = get_llm_interface(engine.config["llm"])
                if engine.llm_interface is None:
                    print("CRITICAL: Failed to recreate llm_interface!")
                    engine = None
            except Exception as llm_error:
                print(f"重新初始化LLM接口失败: {llm_error}")
                import traceback
                traceback.print_exc()
                engine = None
                
    except Exception as e:
        print(f"FATAL: Failed to initialize KimiEngine: {e}")
        # Import traceback to print full stack trace
        import traceback
        traceback.print_exc()
        # For now, let the API start but endpoints will fail
        engine = None

@app.post("/v1/chat/completions", 
          response_model=ChatCompletionResponse, 
          summary="OpenAI Compatible Chat Completion",
          tags=["Chat"])
def create_chat_completion(request: ChatCompletionRequest):
    """
    Handles chat completion requests in an OpenAI-compatible format.

    Note: Streaming is not currently supported.
    Note: `model` in request is ignored; the engine's loaded model is used.
    """
    if engine is None:
        raise HTTPException(status_code=503, detail="KimiEngine not initialized. Check server logs.")
    
    if engine.llm_interface is None:
        logger.error("KimiEngine has no LLM interface. This might be due to a reset operation.")
        raise HTTPException(status_code=503, detail="KimiEngine not fully initialized. Try again in a moment.")

    if request.stream:
        raise HTTPException(status_code=400, detail="Streaming responses are not supported in this version.")

    request_id = f"chatcmpl-{uuid.uuid4()}"
    created_time = int(time.time())

    # --- Simulate conversation history processing --- 
    # The current KimiEngine manages history internally via ingest/chat.
    # For a stateless API like OpenAI's, we need to reconstruct the state 
    # or adapt KimiEngine to accept history directly.
    
    # Simple approach for now: Reset engine, ingest system/doc prompts, then run user query.
    # This is INEFFICIENT for multi-turn conversations via API.
    # A better approach would modify KimiEngine to accept message history.
    try:
        engine.reset()
        logger.info("Engine reset successfully")
    except Exception as e:
        logger.error(f"Error resetting engine: {e}")
        import traceback
        traceback.print_exc()
        # 如果reset失败但engine和llm_interface仍然存在，可以继续
        if engine is None or engine.llm_interface is None:
            raise HTTPException(status_code=503, detail="Failed to reset KimiEngine. Try again later.")
    
    last_user_message = None
    for message in request.messages:
        if message.role == "system":
            # Ingest system messages (potentially long documents)
            print(f"Ingesting system message (length {len(message.content)})...")
            engine.ingest(message.content)
        elif message.role == "user":
            # Keep track of the last user message to run chat
            last_user_message = message.content
        elif message.role == "assistant":
            # Add assistant messages to history *after* potential ingest
            # This assumes assistant messages don't trigger ingest
            engine.conversation_history.append(message.dict())

    if not last_user_message:
        raise HTTPException(status_code=400, detail="No user message found in the request.")

    # --- Generate completion using the last user message --- 
    try:
        print(f"Running chat for user message: {last_user_message[:50]}...")
        completion_text = engine.chat(last_user_message)
    except Exception as e:
        print(f"Error during engine.chat: {e}")
        # Log the full traceback
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error generating completion: {e}")

    # --- Format response --- 
    response_message = ChatMessage(role="assistant", content=completion_text)
    choice = ChatCompletionChoice(index=0, message=response_message, finish_reason="stop")
    
    # Placeholder for usage calculation
    usage = CompletionUsage(
        prompt_tokens=engine.token_counter.count_tokens(last_user_message), # Simplified
        completion_tokens=engine.token_counter.count_tokens(completion_text), # Simplified
        total_tokens=engine.token_counter.count_tokens(last_user_message) + engine.token_counter.count_tokens(completion_text) # Simplified
    )

    return ChatCompletionResponse(
        id=request_id,
        created=created_time,
        model=engine_model_name, 
        choices=[choice],
        usage=usage
    )

@app.get("/api/suggestions", 
         summary="Get dynamic suggestion prompts", 
         tags=["Suggestions"])
async def get_suggestions():
    """
    Fetches suggestion prompts from an external source.
    """
    suggestions_url = "https://openkimi.chieko.seren.living/news"
    default_suggestions = [
        {"title": "如何写一份出色的商业计划书？", "icon": "document-text-outline"},
        {"title": "解释量子计算的基本原理。", "icon": "hardware-chip-outline"},
        {"title": "给我一些关于地中海饮食的建议。", "icon": "restaurant-outline"},
        {"title": "比较Python和JavaScript的主要区别。", "icon": "code-slash-outline"},
        {"title": "如何有效地学习一门新语言？", "icon": "language-outline"},
        {"title": "当前全球经济面临的主要挑战是什么？", "icon": "trending-up-outline"}
    ]
    try:
        response = requests.get(suggestions_url, timeout=5) # Add timeout
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        data = response.json()
        
        # Assuming the API returns a list of objects, each with a 'title' field.
        # Adjust parsing based on the actual API response structure.
        if isinstance(data, list) and len(data) > 0:
            suggestions = []
            for item in data:
                # Try to find a title-like field
                title = item.get('title') or item.get('name') or item.get('headline')
                if title and isinstance(title, str):
                    # Assign a default icon or try to guess based on keywords?
                    icon = item.get('icon', 'newspaper-outline') # Default icon
                    suggestions.append({"title": title.strip(), "icon": icon})
                if len(suggestions) >= 6: # Limit to 6 suggestions like the original UI
                    break 
            if suggestions: # If we got any valid suggestions
                return JSONResponse(content=suggestions)
            else:
                print(f"Warning: Fetched data from {suggestions_url} but couldn't extract valid titles. Using defaults.")
                return JSONResponse(content=default_suggestions)
        else:
            print(f"Warning: Fetched data from {suggestions_url} is not a non-empty list. Using defaults.")
            return JSONResponse(content=default_suggestions)

    except requests.exceptions.RequestException as e:
        print(f"Error fetching suggestions from {suggestions_url}: {e}. Using defaults.")
        return JSONResponse(content=default_suggestions)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from {suggestions_url}: {e}. Using defaults.")
        return JSONResponse(content=default_suggestions)
    except Exception as e:
        print(f"An unexpected error occurred while fetching suggestions: {e}. Using defaults.")
        return JSONResponse(content=default_suggestions)

@app.get("/health", summary="Health Check", tags=["Management"])
def health_check():
    """Basic health check endpoint."""
    if engine is not None and engine.llm_interface is not None:
         return {"status": "ok", "engine_initialized": True, "model_name": engine_model_name}
    else:
         return {"status": "error", "engine_initialized": False, "detail": "KimiEngine failed to initialize."}

# 处理文件上传
@app.post("/v1/files/upload", tags=["Files"])
async def upload_file(file: UploadFile = File(...)):
    """上传文件到服务器"""
    if engine is None:
        raise HTTPException(status_code=503, detail="KimiEngine not initialized. Check server logs.")
    
    # 检查文件格式
    filename = file.filename
    file_extension = filename.split(".")[-1].lower()
    allowed_extensions = ["pdf", "docx", "txt", "doc"]
    
    if file_extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"不支持的文件格式: {file_extension}。支持的格式: {', '.join(allowed_extensions)}")
    
    # 生成唯一文件ID
    file_id = str(uuid.uuid4())
    
    # 创建文件存储路径
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}_{filename}")
    
    try:
        # 保存上传的文件
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        
        # 存储文件信息
        uploaded_files[file_id] = {
            "file_id": file_id,
            "filename": filename,
            "path": file_path,
            "status": "uploaded",
            "timestamp": time.time()
        }
        
        logger.info(f"文件已上传: {filename}, ID: {file_id}")
        
        return {"status": "success", "file_id": file_id, "filename": filename}
    
    except Exception as e:
        logger.error(f"文件上传失败: {e}")
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")

# 处理文件摄入
@app.post("/v1/files/ingest", tags=["Files"])
async def ingest_file(file_data: dict, background_tasks: BackgroundTasks):
    """将文件内容摄入到KimiEngine"""
    if engine is None:
        raise HTTPException(status_code=503, detail="KimiEngine not initialized. Check server logs.")
    
    file_id = file_data.get("file_id")
    if not file_id or file_id not in uploaded_files:
        raise HTTPException(status_code=404, detail=f"文件ID不存在: {file_id}")
    
    file_info = uploaded_files[file_id]
    file_path = file_info["path"]
    filename = file_info["filename"]
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"文件不存在: {filename}")
    
    try:
        # 更新文件状态
        uploaded_files[file_id]["status"] = "processing"
        
        # 处理不同类型的文件
        file_extension = filename.split(".")[-1].lower()
        
        if file_extension == "pdf":
            background_tasks.add_task(process_pdf, file_id, file_path)
            return {"status": "processing", "file_id": file_id, "message": "PDF文件正在处理中"}
        
        elif file_extension in ["docx", "doc"]:
            background_tasks.add_task(process_docx, file_id, file_path)
            return {"status": "processing", "file_id": file_id, "message": "Word文档正在处理中"}
        
        elif file_extension == "txt":
            background_tasks.add_task(process_txt, file_id, file_path)
            return {"status": "processing", "file_id": file_id, "message": "文本文件正在处理中"}
        
        else:
            raise HTTPException(status_code=400, detail=f"不支持的文件类型: {file_extension}")
    
    except Exception as e:
        logger.error(f"文件摄入失败: {e}")
        uploaded_files[file_id]["status"] = "error"
        raise HTTPException(status_code=500, detail=f"文件摄入失败: {str(e)}")

# 获取文件状态
@app.get("/v1/files/{file_id}/status", tags=["Files"])
async def get_file_status(file_id: str):
    """获取文件处理状态"""
    if file_id not in uploaded_files:
        raise HTTPException(status_code=404, detail=f"文件ID不存在: {file_id}")
    
    return uploaded_files[file_id]

# 处理PDF文件
async def process_pdf(file_id: str, file_path: str):
    """处理PDF文件并摄入到KimiEngine"""
    try:
        # 尝试导入PyPDF2
        try:
            import PyPDF2
        except ImportError:
            logger.error("PyPDF2库未安装，无法处理PDF文件")
            uploaded_files[file_id]["status"] = "error"
            return
        
        with open(file_path, "rb") as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text_content = ""
            
            # 提取每一页的文本
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text_content += page.extract_text() + "\n\n"
        
        # 摄入文本到KimiEngine
        if text_content:
            engine.ingest(text_content)
            uploaded_files[file_id]["status"] = "ingested"
            logger.info(f"PDF文件已成功摄入: {file_id}")
        else:
            logger.warning(f"PDF文件内容为空: {file_id}")
            uploaded_files[file_id]["status"] = "empty"
    
    except Exception as e:
        logger.error(f"处理PDF文件时出错: {e}")
        uploaded_files[file_id]["status"] = "error"
        uploaded_files[file_id]["error"] = str(e)

# 处理Word文档
async def process_docx(file_id: str, file_path: str):
    """处理Word文档并摄入到KimiEngine"""
    try:
        # 尝试导入docx库
        try:
            import docx
        except ImportError:
            logger.error("docx库未安装，无法处理Word文档")
            uploaded_files[file_id]["status"] = "error"
            return
        
        doc = docx.Document(file_path)
        text_content = ""
        
        # 提取文档中的段落文本
        for para in doc.paragraphs:
            text_content += para.text + "\n"
        
        # 摄入文本到KimiEngine
        if text_content:
            engine.ingest(text_content)
            uploaded_files[file_id]["status"] = "ingested"
            logger.info(f"Word文档已成功摄入: {file_id}")
        else:
            logger.warning(f"Word文档内容为空: {file_id}")
            uploaded_files[file_id]["status"] = "empty"
    
    except Exception as e:
        logger.error(f"处理Word文档时出错: {e}")
        uploaded_files[file_id]["status"] = "error"
        uploaded_files[file_id]["error"] = str(e)

# 处理纯文本文件
async def process_txt(file_id: str, file_path: str):
    """处理纯文本文件并摄入到KimiEngine"""
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            text_content = file.read()
        
        # 摄入文本到KimiEngine
        if text_content:
            engine.ingest(text_content)
            uploaded_files[file_id]["status"] = "ingested"
            logger.info(f"文本文件已成功摄入: {file_id}")
        else:
            logger.warning(f"文本文件内容为空: {file_id}")
            uploaded_files[file_id]["status"] = "empty"
    
    except Exception as e:
        logger.error(f"处理文本文件时出错: {e}")
        uploaded_files[file_id]["status"] = "error"
        uploaded_files[file_id]["error"] = str(e)

def cli():
    parser = argparse.ArgumentParser(description="Run the OpenKimi FastAPI Server.")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind the server to.")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind the server to.")
    parser.add_argument("--config", "-c", type=str, default=None, help="Path to KimiEngine JSON config file.")
    # Add args to potentially override engine settings if needed
    # parser.add_argument("--model", "-m", type=str, default=None, help="Override model path/name in config.")
    parser.add_argument("--mcp-candidates", type=int, default=1, help="Number of MCP candidates (1 to disable MCP).")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reloading for development.")

    args = parser.parse_args()
    
    # Initialize the engine *before* starting uvicorn
    initialize_engine(args)
    
    print(f"Starting OpenKimi API server on {args.host}:{args.port}")
    uvicorn.run(
        "openkimi.api.server:app", 
        host=args.host, 
        port=args.port, 
        reload=args.reload, 
        log_level="info"
    )

if __name__ == "__main__":
    # This allows running the server directly using `python -m openkimi.api.server`
    cli() 