import time
import uuid
import os
import argparse
import sys
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse # For future streaming
import uvicorn

# Add project root to sys.path to allow importing openkimi
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from openkimi import KimiEngine
from openkimi.api.models import ChatCompletionRequest, ChatCompletionResponse, ChatMessage, ChatCompletionChoice, CompletionUsage

app = FastAPI(
    title="OpenKimi API",
    description="OpenAI-compatible API for the OpenKimi long context engine.",
    version="0.1.0"
)

# Global variable to hold the KimiEngine instance
# This is simple; for production, consider dependency injection frameworks
engine: Optional[KimiEngine] = None
engine_model_name: str = "openkimi-engine"

def initialize_engine(args):
    """Initializes the global KimiEngine based on args."""
    global engine, engine_model_name
    print("Initializing Kimi Engine for API server...")
    try:
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
    except Exception as e:
        print(f"FATAL: Failed to initialize KimiEngine: {e}")
        # You might want to exit here if the engine is critical
        # sys.exit(1)
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
    engine.reset() 
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

@app.get("/health", summary="Health Check", tags=["Management"])
def health_check():
    """Basic health check endpoint."""
    if engine is not None and engine.llm_interface is not None:
         return {"status": "ok", "engine_initialized": True, "model_name": engine_model_name}
    else:
         return {"status": "error", "engine_initialized": False, "detail": "KimiEngine failed to initialize."}

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