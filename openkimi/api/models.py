from pydantic import BaseModel, Field, EmailStr
from typing import List, Dict, Optional, Union
from datetime import datetime

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
    session_id: Optional[str] = Field(None, description="会话ID，用于保持会话状态")

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
    session_id: Optional[str] = Field(None, description="会话ID，用于保持会话状态")

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

# ============= 用户和认证相关模型 =============

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr = Field(...)

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)
    is_admin: Optional[bool] = False

class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=6)
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None

class UserResponse(UserBase):
    id: int
    is_active: bool
    is_admin: bool
    created_at: datetime
    
    class Config:
        orm_mode = True

# ============= API密钥相关模型 =============

class APIKeyBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None

class APIKeyCreate(APIKeyBase):
    expires_at: Optional[datetime] = None

class APIKeyResponse(APIKeyBase):
    id: int
    key: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    is_active: bool
    last_used_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True

# ============= 使用统计相关模型 =============

class UsageStatistics(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

class DateRangeRequest(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

# ============= 错误响应模型 =============

class ErrorResponse(BaseModel):
    detail: str 

# ============= 会话管理相关模型 =============

class SessionResponse(BaseModel):
    session_id: str = Field(..., description="会话ID")
    created_at: int = Field(..., description="创建时间戳")
    last_accessed: int = Field(..., description="最后访问时间戳")
    expires_at: int = Field(..., description="过期时间戳") 