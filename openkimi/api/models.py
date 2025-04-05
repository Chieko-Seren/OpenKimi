from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Union

# Based on OpenAI Chat Completion API

class ChatMessage(BaseModel):
    role: str = Field(..., description="'system', 'user', or 'assistant'")
    content: str = Field(..., description="The message content")

class ChatCompletionRequest(BaseModel):
    model: str = Field(..., description="The model to use (currently ignored, uses engine's model)")
    messages: List[ChatMessage] = Field(..., description="A list of messages comprising the conversation history")
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 512
    # Add other common OpenAI params if needed (top_p, frequency_penalty, etc.)
    stream: Optional[bool] = False # Streaming not implemented in this version

class ChoiceDelta(BaseModel):
    content: Optional[str] = None

class CompletionUsage(BaseModel):
    prompt_tokens: int = 0 # Placeholder
    completion_tokens: int = 0 # Placeholder
    total_tokens: int = 0 # Placeholder

class ChatCompletionChoice(BaseModel):
    index: int = 0
    message: Optional[ChatMessage] = None
    delta: Optional[ChoiceDelta] = None # For streaming
    finish_reason: Optional[str] = "stop" # e.g., "stop", "length"

class ChatCompletionResponse(BaseModel):
    id: str = Field(..., description="A unique identifier for the chat completion")
    object: str = "chat.completion" # Fixed value
    created: int = Field(..., description="Unix timestamp of creation")
    model: str = Field(..., description="The model used for the completion")
    choices: List[ChatCompletionChoice]
    usage: Optional[CompletionUsage] = None # Placeholder

class ChatCompletionChunkChoice(BaseModel):
    index: int = 0
    delta: ChoiceDelta
    finish_reason: Optional[str] = None

class ChatCompletionChunk(BaseModel):
    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str
    choices: List[ChatCompletionChunkChoice] 