import time
import uuid
import os
import argparse
import sys
import logging
import shutil
from typing import Optional, List, Any, Dict, Literal, Union
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends, BackgroundTasks, status
from fastapi.responses import StreamingResponse, JSONResponse # Add JSONResponse
from fastapi.middleware.cors import CORSMiddleware  # 导入CORS中间件
import uvicorn
import requests # Import requests
import json # Import json
from sqlalchemy.orm import Session
from sqlalchemy import text
from pathlib import Path
from tempfile import SpooledTemporaryFile

# Setup logging
logger = logging.getLogger(__name__)

# Add project root to sys.path to allow importing openkimi
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from openkimi import KimiEngine
from openkimi.utils.llm_interface import get_llm_interface
from openkimi.api.models import (
    ChatCompletionRequest, ChatCompletionResponse, ChatMessage, ChatCompletionChoice, 
    CompletionUsage, UserCreate, UserUpdate, UserResponse, APIKeyCreate, APIKeyResponse,
    UsageStatistics, DateRangeRequest, ErrorResponse
)
from openkimi.api.database import get_db, create_tables, create_api_key, get_all_api_keys, revoke_api_key, record_api_usage, get_user_usage, User, APIKey, UsageRecord
from openkimi.api.auth import get_api_key, get_admin_user, create_user, authenticate_user, create_default_admin, user_to_response, apikey_to_response, hash_password

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

# 应用启动事件：初始化数据库
@app.on_event("startup")
async def startup_db_client():
    try:
        # 创建数据库表
        create_tables()
        # 创建默认管理员用户
        db = next(get_db())
        create_default_admin(db)
        logger.info("数据库和默认管理员用户初始化成功")
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        import traceback
        traceback.print_exc()

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
def create_chat_completion(
    request: ChatCompletionRequest,
    api_key: Any = Depends(get_api_key),
    db: Session = Depends(get_db)
):
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
        
        # 记录API使用情况
        prompt_tokens = engine.token_counter.count_tokens(last_user_message)
        completion_tokens = engine.token_counter.count_tokens(completion_text)
        try:
            record_api_usage(
                db=db, 
                user_id=api_key.user_id, 
                api_key_id=api_key.id, 
                endpoint="/v1/chat/completions", 
                prompt_tokens=prompt_tokens, 
                completion_tokens=completion_tokens
            )
        except Exception as usage_error:
            logger.error(f"记录API使用情况失败: {usage_error}")
            
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

@app.post("/v1/web_search", 
          summary="Web Search API",
          tags=["Tools"])
async def web_search(search_data: dict):
    """
    执行网络搜索，并返回搜索结果
    """
    if engine is None:
        raise HTTPException(status_code=503, detail="KimiEngine not initialized. Check server logs.")
    
    query = search_data.get("query")
    if not query:
        raise HTTPException(status_code=400, detail="查询参数为空")
    
    try:
        # 使用Google Search API（或其他搜索API）
        # 这里简化实现，实际应该集成真正的搜索API
        search_url = f"https://www.googleapis.com/customsearch/v1"
        params = {
            "q": query,
            # 实际使用时需添加API密钥等参数
            # "key": GOOGLE_API_KEY,
            # "cx": GOOGLE_SEARCH_ENGINE_ID,
        }
        
        # 尝试使用开源搜索引擎
        search_results = await search_with_duckduckgo(query)
        
        # 如果DuckDuckGo搜索失败，尝试使用SearX
        if not search_results:
            search_results = await search_with_searx(query)
        
        # 如果所有真实搜索都失败，则使用模拟结果
        if not search_results:
            # 模拟搜索结果
            search_results = [
                {
                    "title": f"关于'{query}'的搜索结果1",
                    "link": f"https://example.com/result1?q={query}",
                    "snippet": f"这是关于'{query}'的一些信息...",
                },
                {
                    "title": f"关于'{query}'的搜索结果2",
                    "link": f"https://example.com/result2?q={query}",
                    "snippet": f"这里有更多关于'{query}'的详细内容...",
                },
                {
                    "title": f"'{query}'的最新资讯",
                    "link": f"https://example.com/news?q={query}",
                    "snippet": f"最新的'{query}'相关新闻和更新...",
                }
            ]
        
        # 存储搜索结果到会话
        ingest_text = f"网络搜索'{query}'的结果:\n\n"
        for i, result in enumerate(search_results):
            ingest_text += f"{i+1}. {result['title']}\n{result['link']}\n{result['snippet']}\n\n"
        
        # 将搜索结果摄入到引擎（可选）
        engine.ingest(ingest_text)
        
        return {
            "status": "success",
            "query": query,
            "results": search_results
        }
    
    except Exception as e:
        logger.error(f"搜索失败: {e}")
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")

# 使用DuckDuckGo搜索(无需API密钥的开源搜索引擎)
async def search_with_duckduckgo(query, num_results=5):
    try:
        import requests
        from bs4 import BeautifulSoup
        import urllib.parse
        
        # 使用DuckDuckGo Lite版本，更容易解析
        encoded_query = urllib.parse.quote_plus(query)
        url = f"https://lite.duckduckgo.com/lite/?q={encoded_query}"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        results = []
        
        # 在DuckDuckGo Lite中，结果在带有class="result-link"的<a>元素中
        links = soup.select("a.result-link")
        snippets = soup.select(".result-snippet")
        
        for i, (link, snippet) in enumerate(zip(links, snippets)):
            if i >= num_results:
                break
                
            title = link.get_text(strip=True)
            href = link.get("href")
            snippet_text = snippet.get_text(strip=True)
            
            results.append({
                "title": title,
                "link": href,
                "snippet": snippet_text
            })
        
        return results
    except Exception as e:
        logger.error(f"DuckDuckGo搜索失败: {e}")
        return []

# 使用SearX搜索(开源元搜索引擎)
async def search_with_searx(query, num_results=5):
    try:
        import requests
        import random
        
        # 公共的SearX实例列表
        # 这些实例可能随时变化，可以从 https://searx.space/ 获取最新列表
        searx_instances = [
            "https://searx.be/search",
            "https://search.mdosch.de/search", 
            "https://searx.fmac.xyz/search"
        ]
        
        # 随机选择一个实例以避免负载集中
        instance_url = random.choice(searx_instances)
        
        params = {
            "q": query,
            "format": "json",
            "language": "zh-CN",
            "categories": "general",
            "time_range": "",
            "safesearch": 1,
            "engines": "wikipedia,bing,duckduckgo",
        }
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        response = requests.get(instance_url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        results = []
        
        if "results" in data:
            for i, result in enumerate(data["results"]):
                if i >= num_results:
                    break
                    
                results.append({
                    "title": result.get("title", "无标题"),
                    "link": result.get("url", "#"),
                    "snippet": result.get("content", "无描述")
                })
        
        return results
    except Exception as e:
        logger.error(f"SearX搜索失败: {e}")
        return []

@app.post("/v1/chat/completions/cot", 
          response_model=ChatCompletionResponse,
          summary="Chain-of-Thought Chat Completion",
          tags=["Chat"])
async def create_cot_chat_completion(request: ChatCompletionRequest):
    """
    使用Chain-of-Thought提示词增强的聊天完成功能
    """
    # 添加详细日志以便调试
    logger.info("接收到CoT请求。检查引擎状态...")
    logger.info(f"引擎状态: {'已初始化' if engine is not None else '未初始化'}")
    if engine is not None:
        logger.info(f"LLM接口状态: {'已初始化' if engine.llm_interface is not None else '未初始化'}")
    
    if engine is None:
        logger.error("严重错误: KimiEngine未初始化，无法处理CoT请求")
        raise HTTPException(status_code=503, detail="KimiEngine not initialized. Check server logs.")
    
    if engine.llm_interface is None:
        logger.error("严重错误: KimiEngine的LLM接口未初始化，可能是reset操作导致或初始化失败")
        # 尝试重新初始化LLM接口
        logger.info("尝试重新初始化LLM接口...")
        try:
            from openkimi.utils.llm_interface import get_llm_interface
            engine.llm_interface = get_llm_interface(engine.config["llm"])
            if engine.llm_interface is None:
                logger.error("LLM接口重新初始化失败")
                raise HTTPException(status_code=503, detail="KimiEngine not fully initialized and repair attempt failed. Try again in a moment.")
            else:
                logger.info("LLM接口重新初始化成功")
        except Exception as e:
            logger.error(f"尝试修复LLM接口时出错: {e}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=503, detail=f"KimiEngine not fully initialized. Repair attempt failed: {e}")

    if request.stream:
        raise HTTPException(status_code=400, detail="Streaming responses are not supported in this version.")

    request_id = f"chatcmpl-{uuid.uuid4()}"
    created_time = int(time.time())
    
    # 处理与常规聊天相同，但添加CoT提示词
    try:
        logger.info("重置引擎状态用于CoT处理...")
        engine.reset()
        logger.info("引擎重置成功")
    except Exception as e:
        logger.error(f"重置引擎时出错: {e}")
        import traceback
        traceback.print_exc()
        # 检查重置后的引擎状态
        logger.info(f"重置后引擎状态: engine={engine is not None}, llm_interface={engine.llm_interface is not None if engine else 'N/A'}")
        if engine is None or engine.llm_interface is None:
            raise HTTPException(status_code=503, detail=f"Failed to reset KimiEngine: {e}. Try again later.")
    
    # CoT系统提示词
    cot_system_prompt = """
# Multiple-CoT

## Role

You are an expert AI assistant capable of gradually explaining the reasoning process.

## First Think step


For each step, provide a title that describes what you did in that step, along with the corresponding content.
Decide whether another step is needed or if you are ready to give the final answer.
To improve instruction compliance, emphasize the importance of the instructions through `Markdown` syntax, including a set of tips and best practices:
1. Use as many **reasoning steps** as possible. At least 3 steps.
2. Be aware of your limitations as an AI and what you can and cannot do.
3. Include exploration of alternative answers. Consider that you might be wrong and where the error might be if your reasoning is incorrect.
4. When you say you are rechecking, actually recheck and use another method. Don't just say you are rechecking.
5. Use at least 3 methods to arrive at the answer.
6. Use best practices.

## Second Think step


For each step mentioned in the previous text, initiate a small sub-step within each step to verify its correctness. After completing each step, start a `reviewer CoT` to review the current step from different perspectives.
1. Use as many **reasoning steps** as possible. At least three steps.
2. Be aware of your limitations as an AI and what you can and cannot do.
3. Include exploring alternative answers. Consider that you might be wrong and where the error might be if your reasoning is incorrect.
    """
    
    # 添加CoT系统提示词
    engine.ingest(cot_system_prompt)
    
    last_user_message = None
    for message in request.messages:
        if message.role == "system":
            # 已经添加了COT提示词，可以再添加用户的系统提示词
            engine.ingest(message.content)
        elif message.role == "user":
            # 保存最后的用户消息
            last_user_message = message.content
        elif message.role == "assistant":
            # 添加助手消息到历史
            engine.conversation_history.append(message.dict())

    if not last_user_message:
        raise HTTPException(status_code=400, detail="No user message found in the request.")

    # 生成回复
    try:
        print(f"Running CoT chat for user message: {last_user_message[:50]}...")
        completion_text = engine.chat(last_user_message)
    except Exception as e:
        print(f"Error during CoT engine.chat: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error generating CoT completion: {e}")

    # 格式化响应
    response_message = ChatMessage(role="assistant", content=completion_text)
    choice = ChatCompletionChoice(index=0, message=response_message, finish_reason="stop")
    
    usage = CompletionUsage(
        prompt_tokens=engine.token_counter.count_tokens(last_user_message), 
        completion_tokens=engine.token_counter.count_tokens(completion_text), 
        total_tokens=engine.token_counter.count_tokens(last_user_message) + engine.token_counter.count_tokens(completion_text)
    )

    return ChatCompletionResponse(
        id=request_id,
        created=created_time,
        model=f"{engine_model_name}-cot", 
        choices=[choice],
        usage=usage
    )

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

# ================ 用户管理路由 ================

@app.post("/api/users", 
         response_model=UserResponse, 
         status_code=status.HTTP_201_CREATED,
         summary="创建新用户",
         tags=["用户管理"])
async def create_new_user(
    user: UserCreate,
    admin: Any = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """创建新用户（需要管理员权限）"""
    try:
        db_user = create_user(db, user)
        return user_to_response(db_user)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"创建用户失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建用户失败: {str(e)}")

@app.get("/api/users/me", 
        response_model=UserResponse,
        summary="获取当前用户信息",
        tags=["用户管理"])
async def get_current_user(
    api_key: Any = Depends(get_api_key),
    db: Session = Depends(get_db)
):
    """获取当前API密钥关联的用户信息"""
    user = db.query(User).filter(User.id == api_key.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user_to_response(user)

@app.get("/api/users", 
        response_model=List[UserResponse],
        summary="获取所有用户",
        tags=["用户管理"])
async def get_all_users(
    admin: Any = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """获取所有用户（需要管理员权限）"""
    users = db.query(User).all()
    return [user_to_response(user) for user in users]

@app.put("/api/users/{user_id}", 
        response_model=UserResponse,
        summary="更新用户信息",
        tags=["用户管理"])
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    admin: Any = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """更新用户信息（需要管理员权限）"""
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 更新用户字段
    if user_update.username is not None:
        # 检查用户名是否已存在
        existing = db.query(User).filter(User.username == user_update.username).first()
        if existing and existing.id != user_id:
            raise HTTPException(status_code=400, detail="用户名已存在")
        db_user.username = user_update.username
    
    if user_update.email is not None:
        # 检查邮箱是否已存在
        existing = db.query(User).filter(User.email == user_update.email).first()
        if existing and existing.id != user_id:
            raise HTTPException(status_code=400, detail="邮箱已存在")
        db_user.email = user_update.email
    
    if user_update.password is not None:
        db_user.hashed_password = hash_password(user_update.password)
    
    if user_update.is_active is not None:
        db_user.is_active = user_update.is_active
    
    if user_update.is_admin is not None:
        db_user.is_admin = user_update.is_admin
    
    db.commit()
    db.refresh(db_user)
    return user_to_response(db_user)

# ================ API密钥管理路由 ================

@app.post("/api/keys", 
         response_model=APIKeyResponse, 
         status_code=status.HTTP_201_CREATED,
         summary="创建API密钥",
         tags=["API密钥"])
async def create_new_api_key(
    key_data: APIKeyCreate,
    api_key: Any = Depends(get_api_key),
    db: Session = Depends(get_db)
):
    """为当前用户创建新的API密钥"""
    try:
        new_key = create_api_key(
            db=db, 
            name=key_data.name, 
            user_id=api_key.user_id,
            description=key_data.description,
            expires_at=key_data.expires_at
        )
        return apikey_to_response(new_key)
    except Exception as e:
        logger.error(f"创建API密钥失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建API密钥失败: {str(e)}")

@app.get("/api/keys", 
        response_model=List[APIKeyResponse],
        summary="获取当前用户的API密钥",
        tags=["API密钥"])
async def get_user_api_keys(
    api_key: Any = Depends(get_api_key),
    db: Session = Depends(get_db)
):
    """获取当前用户的所有API密钥"""
    keys = get_all_api_keys(db, api_key.user_id)
    return [apikey_to_response(key) for key in keys]

@app.delete("/api/keys/{key_id}", 
          status_code=status.HTTP_204_NO_CONTENT,
          summary="撤销API密钥",
          tags=["API密钥"])
async def delete_api_key(
    key_id: int,
    api_key: Any = Depends(get_api_key),
    db: Session = Depends(get_db)
):
    """撤销指定的API密钥（只能撤销自己的密钥）"""
    # 不允许撤销当前使用的密钥
    if api_key.id == key_id:
        raise HTTPException(status_code=400, detail="不能撤销当前正在使用的API密钥")
    
    success = revoke_api_key(db, key_id, api_key.user_id)
    if not success:
        raise HTTPException(status_code=404, detail="API密钥不存在或不属于当前用户")
    return None

# ================ 使用统计路由 ================

@app.post("/api/usage", 
         response_model=UsageStatistics,
         summary="获取API使用统计",
         tags=["统计"])
async def get_api_usage(
    date_range: DateRangeRequest,
    api_key: Any = Depends(get_api_key),
    db: Session = Depends(get_db)
):
    """获取当前用户的API使用统计"""
    usage = get_user_usage(db, api_key.user_id, date_range.start_date, date_range.end_date)
    return UsageStatistics(**usage)

@app.get("/api/health", 
        summary="API健康检查",
        tags=["系统"])
async def api_health_check(
    db: Session = Depends(get_db)
):
    """API服务健康检查，不需要API密钥"""
    try:
        # 尝试数据库连接
        db.execute(text("SELECT 1")).first()
        # 检查Kimi引擎状态
        engine_status = "ok" if engine is not None and engine.llm_interface is not None else "error"
        
        return {
            "status": "ok",
            "database": "ok",
            "engine": engine_status,
            "version": app.version
        }
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return {
            "status": "error",
            "database": "error",
            "engine": "unknown",
            "error": str(e)
        } 